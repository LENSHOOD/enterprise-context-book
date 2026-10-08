"""Local teaching application: shared Python core, durable isolated workspaces.

SQLite commits the simulated business state and task records together. This is
not a transaction coordinator for external queues or a production identity system.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import tempfile

from northstar import NorthstarPlatform, Principal, DEFAULT_FIXTURE_TIME
from modeling import semantic_slice
from intelligence import ContextAssistant, materialize_resources
from model_gateway import ModelGateway, ModelError

DATA = Path(__file__).parents[1] / "data"
ROLES = ("developer", "support", "sre", "incident_commander", "executive", "strategy", "revops", "product")
SCENARIOS = {
    "incident": {"role": "sre", "goal": "判断退款积压并进行一次受控重放",
                 "scope": "northstar / refund-queue；最多重放100条",
                 "completion": "队列下降、错误率不升且观察版本更新；不代表全部退款完成"},
    "change": {"role": "developer", "goal": "修改 order.cancelled 会影响什么",
               "scope": "order.cancelled v2 的消费者与测试",
               "completion": "列出有引用的影响路径及尚未核实的内容，交由开发者复核"},
    "strategy": {"role": "executive", "goal": "H2 的销售情况为什么比 H1 差这么多？",
                 "scope": "northstar全公司，H1/H2-2026，固定教学快照",
                 "completion": "确认指标口径，核对差异和目标，列出假设与缺口供经营负责人复核"},
}


def required_text(payload: dict, key: str, limit: int = 2000) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{key} 必须是1—{limit}个字符的非空文本")
    return value.strip()


def _calculate_source_revision() -> str:
    """Tie stored sessions and displayed code to the exact teaching source."""
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


_SOURCE_REVISION = _calculate_source_revision()


def source_revision() -> str:
    # Bind to the code loaded by this process, not files edited after startup.
    return _SOURCE_REVISION


class Workspace:
    def __init__(self, state: dict | None = None, data_dir: Path = DATA):
        self.state = deepcopy(state) if state else {
            "schema": 1, "seconds": 0, "policy_notes": [], "tasks": {}, "updates": []}
        self.data_dir = data_dir
        self.platform = self._build()
        saved = self.state.get("runtime")
        if saved:
            self._restore_runtime(saved)
        # Changed source fixtures do not silently make existing task evidence current.
        if self.state.get("manifest", self.platform.manifest) != self.platform.manifest:
            for task in self.state["tasks"].values():
                task["stale"] = True

    def now(self):
        return DEFAULT_FIXTURE_TIME + timedelta(seconds=self.state["seconds"])

    def _build(self, extra_release: dict | None = None) -> NorthstarPlatform:
        # Only a private copy is edited; published fixtures remain unchanged.
        with tempfile.TemporaryDirectory(prefix="northstar-build-") as folder:
            data = Path(folder) / "data"
            shutil.copytree(self.data_dir, data)
            if self.state["policy_notes"]:
                policy = data / "raw/business/order-cancellation.md"
                policy.write_text(policy.read_text(encoding="utf-8") + "\n" + "\n".join(
                    self.state["policy_notes"]), encoding="utf-8")
                manifest_path = data / "raw/manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                item = next(x for x in manifest["sources"] if x["id"] == "product-cancellation-policy")
                item["version"] += f"-lab.{len(self.state['policy_notes'])}"
                item["citation"] = f"knowledge://northstar/policy/order-cancellation@{item['version']}"
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            releases = list(self.state.get("intelligence", {}).get("releases", []))
            if extra_release:
                releases.append(extra_release)
            materialize_resources(data, releases)
            return NorthstarPlatform(data, clock=self.now)

    def _runtime(self) -> dict:
        p = self.platform
        pairs = lambda mapping: [[list(key), value] for key, value in mapping.items()]
        return {"runtime": p.runtime, "task_states": pairs(p.task_states),
                "task_operators": pairs(p.task_operators), "previews": p.previews,
                "tokens": p.tokens, "receipts": pairs(p._receipts),
                "receipts_by_id": p._receipts_by_id, "execution_count": p.execution_count,
                "memory_events": pairs(p.memory.events),
                "memory_owners": [[list(key), asdict(value)] for key, value in p.memory.owners.items()]}

    def _restore_runtime(self, saved: dict) -> None:
        p = self.platform
        pairs = lambda rows: {tuple(key): value for key, value in rows}
        for key in ("runtime", "previews", "tokens", "execution_count"):
            setattr(p, key, deepcopy(saved[key]))
        p.task_states = pairs(saved["task_states"])
        p.task_operators = pairs(saved["task_operators"])
        p._receipts = pairs(saved["receipts"])
        p._receipts_by_id = deepcopy(saved["receipts_by_id"])
        p.memory.events = defaultdict(list, pairs(saved["memory_events"]))
        p.memory.owners = {tuple(key): Principal(**value) for key, value in saved["memory_owners"]}

    def snapshot(self) -> dict:
        return deepcopy({**self.state, "manifest": self.platform.manifest, "runtime": self._runtime()})

    @staticmethod
    def principal(role: str) -> Principal:
        if role not in ROLES:
            raise ValueError("未知教学角色")
        return Principal(f"lab-{role}", role)

    def event(self, task: dict, kind: str, actor: Principal, **details) -> None:
        task["events"].append({"sequence": len(task["events"]) + 1, "type": kind,
                               "actor": actor.user_id, "at": self.now().isoformat(), **details})

    def task(self, payload: dict, actor: Principal, approval: bool = False) -> dict:
        task = self.state["tasks"].get(required_text(payload, "task_id", 100))
        if task is None:
            raise ValueError("任务不存在于本实验空间")
        if task["owner"] != asdict(actor) and not (
            approval and actor.role == "incident_commander" and task["kind"] == "incident"
            and task.get("preview")):
            raise PermissionError("当前角色不是任务负责人；事故负责人只能查看动作预览")
        return task

    def task_view(self, task: dict, actor: Principal) -> dict:
        if task["owner"] != asdict(actor):
            return {"id": task["id"], "kind": task["kind"], "preview": task.get("preview"),
                    "state": self.platform.task_states.get((actor.tenant, task["id"]), "opened"),
                    "stale": task["stale"], "approval_only": True}
        view = deepcopy({key: value for key, value in task.items() if key != "token"})
        if task["kind"] == "incident":
            view["state"] = self.platform.task_state(task["id"], actor)
        return view

    def create_task(self, payload: dict, actor: Principal) -> dict:
        kind = payload.get("kind")
        if kind not in SCENARIOS:
            raise ValueError("未知工作线")
        preset = SCENARIOS[kind]
        if actor.role != preset["role"] and not (kind == "strategy" and actor.role in ("strategy", "revops", "product")):
            raise PermissionError(f"这条工作线需要 {preset['role']} 角色")
        if any(payload.get(key) != preset[key] for key in ("scope", "completion")):
            raise ValueError("本实验仅支持页面列明的固定范围与完成条件")
        task_id = "task-" + secrets.token_hex(6)
        task = {"id": task_id, "kind": kind, "owner": asdict(actor), "state": "opened",
                "conditions": {key: required_text(payload, key) for key in ("goal", "scope", "completion")},
                "events": [], "snapshots": [], "stale": False, "package": None}
        task["conditions"]["time"] = ("2027-01-02固定经营快照" if kind == "strategy" else self.now().isoformat())
        self.state["tasks"][task_id] = task
        if kind == "incident":
            self.platform.begin_diagnosis(task_id, actor)
        self.event(task, "task_created", actor)
        return self.task_view(task, actor)

    def context(self, payload: dict, actor: Principal) -> dict:
        task = self.task(payload, actor)
        if task["stale"] and task["kind"] == "incident" and task.get("preview"):
            raise ValueError("资源已更新，旧预览不能继续；请新建事故任务重新诊断与批准")
        kwargs = {}
        if task["kind"] == "strategy":
            kwargs = {"mode": "strategic", "definition_confirmation": task.get("definition_confirmation")}
        elif task["kind"] == "change":
            kwargs = {"graph_seed": "event-order-cancelled", "competency_question_id": "CQ-EVENT-001"}
        else:
            kwargs = {"runtime_resource": "refund-queue"}
        package = self.platform.context(task["conditions"]["goal"], actor, task["id"], **kwargs)
        package["trace_id"] = f"ctx:{actor.tenant}:{task['id']}:{len(task['snapshots']) + 1}"
        package["captured_at"] = self.now().isoformat()
        self.event(task, "context_built", actor, manifest=self.platform.manifest, trace_id=package["trace_id"])
        package["task_conditions"] = deepcopy(task["conditions"])
        package["memories"] = deepcopy(task["events"])
        task["state"] = package.get("status", package.get("task_state", "opened"))
        if task["kind"] == "change":
            task["state"] = "ready_for_review"
        package["task_state"] = (self.platform.task_state(task["id"], actor)
                                 if task["kind"] == "incident" else task["state"])
        task["package"] = package
        task["snapshots"].append(deepcopy(package))
        task["stale"] = False
        return self.task_view(task, actor)

    def update_policy(self, payload: dict, actor: Principal) -> dict:
        if actor.role != "product":
            raise PermissionError("政策维护实验需要 product 角色")
        note = required_text(payload, "note", 500)
        before = self.platform
        old_runtime = self._runtime()
        self.state["policy_notes"].append(note)
        self.platform = self._build()
        self._restore_runtime(old_runtime)
        affected = []
        for task in self.state["tasks"].values():
            task["stale"] = True
            affected.append(task["id"])
        result = {"before_manifest": before.manifest, "after_manifest": self.platform.manifest,
                  "object": self.platform.by_id["product-cancellation-policy"],
                  "evidence": self.platform.search(note, actor), "wiki": self.platform.build_wiki(actor),
                  "invalidated_tasks": affected,
                  "rule": "教学实现保守地标记本空间全部旧任务；旧快照保留，待重新取证"}
        self.state["updates"].append({key: result[key] for key in ("before_manifest", "after_manifest", "invalidated_tasks")})
        return result

    def dispatch(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("请求必须是对象")
        actor = self.principal(payload.get("role", "developer"))
        op = payload.get("op")
        p = self.platform
        if isinstance(op, str) and op.startswith(("assist.", "resource.")):
            return ContextAssistant(self).dispatch(payload, actor)
        if op == "overview":
            tasks = [self.task_view(t, actor) for t in self.state["tasks"].values()
                     if t["owner"] == asdict(actor) or (actor.role == "incident_commander" and t.get("preview"))]
            return {"manifest": p.manifest, "clock": self.now().isoformat(), "tasks": tasks,
                    "source_revision": source_revision(), "simulation": True}
        if op == "resources":
            docs = p.current_documents(actor)
            enterprise = []
            if actor.role in p.strategy_context.data["fixture"]["acl"]:
                enterprise = [{**item, "kind": p.strategy_context.types[item['id']]}
                              for item in p.strategy_context.by_id.values()]
            return {"documents": docs, "enterprise": enterprise, "manifest": p.manifest}
        if op == "search":
            disabled = payload.get("disabled_channels", [])
            if not isinstance(disabled, list) or any(x not in ("bm25", "semantic_proxy") for x in disabled):
                raise ValueError("未知检索通道")
            valid = payload.get("valid_at") or None
            known = payload.get("observed_at") or None
            return {"evidence": p.search(required_text(payload, "question"), actor,
                                          disabled_channels=set(disabled), valid_at=valid, observed_at=known),
                    "authorized_documents": len(p.current_documents(actor, valid_at=valid, observed_at=known)),
                    "degraded_channels": disabled, "manifest": p.manifest}
        if op == "model":
            docs = p.current_documents(actor)
            ids = {d["id"] for d in docs}
            edges = [e for e in p.edges if e["from"] in ids and e["to"] in ids]
            return {"semantic_contract": semantic_slice(p.domain_model, docs, edges), "relations": edges}
        if op == "trace":
            return {"relations": p.trace(required_text(payload, "seed", 150), actor)}
        if op == "wiki":
            return {"wiki": p.build_wiki(actor), "manifest": p.manifest}
        if op == "architecture":
            return p.architecture_consistency(actor)
        if op == "policy.update":
            return self.update_policy(payload, actor)
        if op == "task.create":
            return self.create_task(payload, actor)
        if op == "task.get":
            return self.task_view(self.task(payload, actor, approval=True), actor)
        if op == "task.context":
            return self.context(payload, actor)
        if op == "clock.advance":
            # Deliberate simulation control; never exposed as a business permission.
            self.state["seconds"] += 61
            return {"clock": self.now().isoformat(), "note": "教学时钟推进61秒，既有队列观察和批准可能过期"}
        if op in ("task.note", "task.confirm_definition", "task.review"):
            task = self.task(payload, actor)
            if op == "task.note":
                self.event(task, "reader_note", actor, text=required_text(payload, "note"),
                           evidence_status="user_statement_not_verified")
            elif op == "task.review":
                if task["kind"] == "incident" or task["state"] != "ready_for_review" or task["stale"]:
                    raise ValueError("仅当前版本、待复核的只读分析任务可以登记复核")
                self.event(task, "human_reviewed", actor, text=required_text(payload, "note"))
                task["state"] = "reviewed"
            else:
                if task["kind"] != "strategy" or not task.get("package"):
                    raise ValueError("先读取经营任务的指标契约")
                expected = p.strategy_context.definition_confirmation()
                if payload.get("confirmation") != expected:
                    raise ValueError("请确认页面展示的完整指标契约及其版本")
                task["definition_confirmation"] = expected
                self.event(task, "definition_confirmed", actor, confirmation=expected)
            return self.task_view(task, actor)
        if op in ("action.prepare", "action.confirm", "action.reject", "action.execute", "action.verify"):
            task = self.task(payload, actor, approval=op in ("action.confirm", "action.reject"))
            if task["kind"] != "incident" or task["stale"]:
                raise ValueError("仅当前版本的事故任务可执行动作；资源更新后请重新建任务")
            if op == "action.prepare":
                if not task.get("package"):
                    raise ValueError("先构造诊断上下文，再准备动作")
                task["preview"] = p.prepare_replay(task["id"], "refund-queue", actor)
            elif op in ("action.confirm", "action.reject"):
                preview = task.get("preview")
                if not preview or payload.get("params_hash") != preview["params_hash"]:
                    raise ValueError("预览已变化，请重新查看具体参数")
                if op == "action.confirm":
                    task["token"] = p.confirm(preview["preview_id"], actor)
                else:
                    p.reject(preview["preview_id"], actor)
            elif op == "action.execute":
                task["receipt"] = p.execute_replay(task.get("token", ""), task["id"] + ":replay", actor)
            else:
                if "receipt" not in task:
                    raise ValueError("尚无执行回执")
                task["verification"] = p.verify_replay(task["receipt"]["receipt_id"], actor)
            self.event(task, op, actor)
            return self.task_view(task, actor)
        raise ValueError("未知实验操作；服务不支持任意命令执行")


class WorkspaceStore:
    def __init__(self, path: Path, data_dir: Path = DATA, gateway=None):
        self.path, self.data_dir = path, data_dir
        self.gateway = gateway or ModelGateway()
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, revision TEXT NOT NULL, state TEXT NOT NULL)")

    def create(self) -> str:
        identity = secrets.token_hex(32)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO workspaces VALUES (?, ?, ?)",
                       (identity, source_revision(), json.dumps(Workspace(data_dir=self.data_dir).snapshot())))
        return identity

    def call(self, identity: str, payload: dict) -> dict:
        if isinstance(payload, dict) and payload.get("op") == "assist.step":
            return self.model_step(identity, payload)
        # Reconstruct + mutate + commit in one transaction: two clicks cannot
        # both execute against an uncommitted copy of the simulated queue.
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision, state FROM workspaces WHERE id = ?", (identity,)).fetchone()
            if row is None:
                raise PermissionError("实验空间不存在，请创建新空间")
            if row[0] != source_revision():
                raise ValueError("Python源码已变化，旧实验保留在数据库中；请新建空间，避免混用运行版本")
            workspace = Workspace(json.loads(row[1]), self.data_dir)
            result = workspace.dispatch(payload)
            db.execute("UPDATE workspaces SET state = ? WHERE id = ?",
                       (json.dumps(workspace.snapshot(), ensure_ascii=False), identity))
            return result

    def model_step(self, identity: str, payload: dict) -> dict:
        # Model latency must not hold the SQLite write lock. This teaching CAS
        # checks the whole workspace; production can use per-request revisions.
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT revision, state FROM workspaces WHERE id = ?", (identity,)).fetchone()
        if row is None:
            raise PermissionError("实验空间不存在，请创建新空间")
        if row[0] != source_revision():
            raise ValueError("Python源码已变化，请新建实验空间")
        workspace = Workspace(json.loads(row[1]), self.data_dir)
        actor = workspace.principal(payload.get("role", "developer"))
        assistant = ContextAssistant(workspace)
        record, context = assistant.prepare(payload, actor)
        decision, failure = None, None
        provider = {"mode": record["mode"], "label": "模型调用尚未完成"}
        try:
            decision, provider = self.gateway.decide(record["mode"], context)
        except ModelError as error:
            failure = str(error)
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT revision, state FROM workspaces WHERE id = ?", (identity,)).fetchone()
            if current != row:
                raise ValueError("等待模型期间实验空间发生变化，本次建议未提交；请重新读取后重试")
            result = assistant.apply(payload, actor, decision, provider, failure)
            db.execute("UPDATE workspaces SET state = ? WHERE id = ?",
                       (json.dumps(workspace.snapshot(), ensure_ascii=False), identity))
            return result
