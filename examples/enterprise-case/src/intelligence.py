"""Two bounded assistants: maintain resources and investigate context requests.

No model output is a dispatch payload. Each decision passes an explicit allowlist.
The durable store calls the model outside its write transaction, then checks that
the workspace has not changed before accepting a decision or running a read tool.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import secrets
from context_flow import ContextFlow


DEMO_SOURCE = """# 退款限流核对说明
refund-worker 的排查需要先核对支付方限流窗口，再查看队列和消费者延迟。
本说明记录需要核验的条件，不授予重放权限，也不证明限流就是本次事故原因。
"""
MAX_STEPS = 8


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def text(value, label: str, limit: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label} 必须是1—{limit}个字符的文本")
    return value.strip()


def exact(value, keys: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("模型字段不符合本步约定；没有执行其建议")


def strings(value, label: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 6:
        raise ValueError(f"{label} 必须是最多六项的列表")
    return [text(x, label, 500) for x in value]


def materialize_resources(data: Path, releases: list[dict]) -> None:
    """Build a private source tree from reviewed releases, preserving originals."""
    latest = {r["source"]["id"]: r for r in releases}
    if not latest:
        return
    paths = {"knowledge": "knowledge.json", "manifest": "raw/manifest.json", "edges": "relations.json",
             "concepts": "modeling/concept-model.json", "glossary": "modeling/glossary.json",
             "mappings": "modeling/source-mappings.json", "questions": "modeling/competency-questions.json"}
    values = {key: json.loads((data / path).read_text(encoding="utf-8")) for key, path in paths.items()}
    for release in latest.values():
        source, candidate = release["source"], release["candidate"]
        identity, kind = source["id"], candidate["entity_type"]
        rel = "DESCRIBED_IN_" + kind.upper()
        term_id = "term.lab." + kind.lower()
        concepts = values["concepts"]
        if kind not in concepts["entityTypes"]:
            concepts["entityTypes"][kind] = {"identity": ["source_uri"], "boundedContext": "operations", "glossaryTerm": term_id}
            values["glossary"]["terms"].append({"id": term_id, "canonicalName": kind, "preferredLabel": kind,
                "aliases": [], "definition": candidate["type_description"], "boundedContext": "operations",
                "steward": source["owner"]["user_id"]})
        concepts["relations"][rel] = {"from": "Service", "to": kind, "cardinality": "many_to_many",
            "allowedEvidence": ["asserted"], "meaning": "材料描述该服务，已由维护者核对来源。",
            "positiveExample": "材料明确指出 refund-worker 的排查事项。",
            "negativeExample": "同时检索命中不等于存在调用、因果或授权关系。"}
        revision = "r" + str(source["revision"])
        citation = f"knowledge://northstar/lab/{identity}@{revision}"
        raw_path = f"incoming/{identity}.md"
        (data / "raw/incoming").mkdir(exist_ok=True)
        (data / "raw" / raw_path).write_text(source["text"], encoding="utf-8")
        registered = {"id": identity, "path": raw_path, "parser": "markdown", "entity_type": kind,
            "title": candidate["title"], "kind": "note", "tenant": "northstar", "system": "payment",
            "acl": ["product", "developer", "sre"], "version": revision, "authority": "reviewed_statement",
            "citation": citation, "valid_from": source["at"], "observed_at": source["at"]}
        values["manifest"]["sources"].append(registered)
        values["knowledge"].append({**registered, "lineage": {"derived_from": [citation]}, "text": source["text"]})
        values["edges"].extend({"from": link["from"], "type": rel, "to": identity,
            "evidence_tier": "asserted", "evidence": citation, "quote": link["quote"]} for link in candidate["links"])
        values["mappings"]["mappings"].append({"source": identity, "owner": source["owner"]["user_id"],
            "produces": [kind, rel], "identityRule": "registered source id + revision", "refreshMode": "on_approval"})
        values["questions"]["questions"].append({"id": "CQ-" + identity, "question": candidate["question"],
            "decision": "帮助定位待核验的服务说明，不授予操作权", "requiredEntityTypes": ["Service", kind],
            "requiredRelations": [rel]})
    values["concepts"]["version"] += "+lab." + digest(releases)[:12]
    for key, path in paths.items():
        (data / path).write_text(json.dumps(values[key], ensure_ascii=False), encoding="utf-8")


class ContextAssistant:
    def __init__(self, workspace):
        self.w = workspace
        self.state = workspace.state.setdefault("intelligence", {"requests": {}, "sources": {}, "drafts": {}, "releases": []})

    def catalog(self, actor) -> list[dict]:
        return [{"id": d["id"], "title": d["title"], "entity_type": d["entity_type"]}
                for d in self.w.platform.current_documents(actor)]

    def owned(self, collection: str, identity: str, actor) -> dict:
        item = self.state[collection].get(identity)
        if not item or item["owner"] != asdict(actor):
            raise PermissionError("记录不存在或不属于当前角色")
        return item

    def tools(self, actor) -> list[str]:
        result = ["search", "trace", "wiki", "clarify", "finish"]
        if actor.role == "sre":
            result.append("observe")
        if actor.role in self.w.platform.strategy_context.data["fixture"]["acl"]:
            result.append("metric")
        return result

    def public(self, record: dict) -> dict:
        result = deepcopy(record)
        active_manifest = record.get("after_manifest") if record.get("state") == "published" else record.get("manifest")
        result["stale"] = active_manifest != self.w.platform.manifest
        result["remaining_steps"] = max(0, MAX_STEPS - record.get("attempts", 0))
        return result

    def dispatch(self, payload: dict, actor) -> dict:
        op = payload["op"]
        if op == "assist.list":
            return {"requests": [self.public(r) for r in self.state["requests"].values() if r["owner"] == asdict(actor)],
                    "sources": [deepcopy(s) for s in self.state["sources"].values() if s["owner"] == asdict(actor)],
                    "drafts": [self.public(d) for d in self.state["drafts"].values() if d["owner"] == asdict(actor)]}
        if op == "assist.start":
            mode = payload.get("mode", "fixture")
            if mode not in ("fixture", "http"):
                raise ValueError("未知模型模式")
            record = {"id": "req-" + secrets.token_hex(6), "owner": asdict(actor),
                "goal": text(payload.get("goal"), "问题"), "mode": mode, "state": "drafting",
                "manifest": self.w.platform.manifest, "history": [], "attempts": 0, "snapshots": []}
            self.state["requests"][record["id"]] = record
            return self.public(record)
        if op in ("assist.get", "assist.confirm"):
            record = self.owned("requests", text(payload.get("id"), "请求ID", 100), actor)
            if op == "assist.confirm":
                if record["state"] != "needs_confirmation" or record["manifest"] != self.w.platform.manifest:
                    raise ValueError("没有当前版本的待确认事项，请重新建立请求")
                pending = record["pending"]
                if payload.get("confirmation_hash") != digest(pending):
                    raise ValueError("确认内容已变化，请重新查看")
                answer = text(payload.get("answer"), "确认说明")
                record["answer"] = answer
                if "conditions" in pending:
                    record["conditions"] = pending["conditions"]
                if "metric_contract" in pending:
                    record["metric_confirmation"] = pending["metric_contract"]
                record["history"].append({"event": "human_confirmed", "actor": actor.user_id,
                    "confirmed": deepcopy(pending), "answer": answer, "at": self.w.now().isoformat()})
                record.pop("pending")
                record.pop("confirmation_hash", None)
                record["state"] = "ready"
            return self.public(record)
        if op in ("resource.register", "resource.revise", "resource.propose", "resource.publish", "resource.reject"):
            if actor.role != "product":
                raise PermissionError("本例仅由 product 角色维护和发布新资料")
            if op == "resource.register":
                source = {"id": "source-" + secrets.token_hex(6), "owner": asdict(actor), "revision": 1,
                          "text": text(payload.get("text"), "原始材料", 6000), "at": self.w.now().isoformat(), "history": []}
                self.state["sources"][source["id"]] = source
                return deepcopy(source)
            if op == "resource.revise":
                source = self.owned("sources", text(payload.get("id"), "来源ID", 100), actor)
                source["history"].append({k: deepcopy(source[k]) for k in ("revision", "text", "at")})
                source.update(text=text(payload.get("text"), "原始材料", 6000), revision=source["revision"] + 1,
                              at=self.w.now().isoformat())
                return deepcopy(source)
            if op == "resource.propose":
                source = self.owned("sources", text(payload.get("id"), "来源ID", 100), actor)
                if any(r["source"]["id"] == source["id"] and r["source"]["revision"] == source["revision"] for r in self.state["releases"]):
                    raise ValueError("该来源版本已经发布；请先修订原文")
                mode = payload.get("mode", "fixture")
                if mode not in ("fixture", "http"):
                    raise ValueError("未知模型模式")
                draft = {"id": "draft-" + secrets.token_hex(6), "owner": asdict(actor), "source": deepcopy(source),
                    "mode": mode, "manifest": self.w.platform.manifest, "state": "drafting", "attempts": 0, "history": []}
                self.state["drafts"][draft["id"]] = draft
                return self.public(draft)
            draft = self.owned("drafts", text(payload.get("id"), "草案ID", 100), actor)
            if draft["state"] == "published":
                return self.public(draft)
            if draft["state"] != "needs_review":
                raise ValueError("仅校验完成的候选可以审核")
            if op == "resource.reject":
                draft.update(state="rejected", review_note=text(payload.get("note"), "审核说明"))
                return self.public(draft)
            source = self.owned("sources", draft["source"]["id"], actor)
            if source["revision"] != draft["source"]["revision"] or draft["manifest"] != self.w.platform.manifest:
                raise ValueError("原文或资源版本已变化，请重新提出候选")
            if payload.get("confirmation_hash") != draft["confirmation_hash"]:
                raise ValueError("候选确认散列不匹配")
            note = text(payload.get("note"), "审核说明")
            release = {"source": deepcopy(draft["source"]), "candidate": deepcopy(draft["candidate"]),
                       "reviewer": asdict(actor), "note": note, "at": self.w.now().isoformat()}
            new_platform = self.w._build(extra_release=release)
            saved_runtime = self.w._runtime()
            self.state["releases"].append(release)
            self.w.platform = new_platform
            self.w._restore_runtime(saved_runtime)
            for task in self.w.state["tasks"].values():
                task["stale"] = True
            draft.update(state="published", review_note=note, after_manifest=new_platform.manifest,
                         published_object=deepcopy(new_platform.by_id[source["id"]]),
                         wiki=new_platform.build_wiki(actor))
            return self.public(draft)
        raise ValueError("未知智能辅助操作")

    def prepare(self, payload: dict, actor) -> tuple[dict, dict]:
        collection = "drafts" if payload.get("kind") == "resource" else "requests"
        record = self.owned(collection, text(payload.get("id"), "记录ID", 100), actor)
        if record["state"] not in ("drafting", "ready"):
            raise ValueError("当前步骤需要确认或已经结束")
        if record["attempts"] >= MAX_STEPS:
            raise ValueError("已达到八步预算；请检查已有材料并新建较小的请求")
        if record["manifest"] != self.w.platform.manifest:
            raise ValueError("资源版本已变化；旧记录保留，请新建请求或候选")
        if collection == "drafts":
            source = self.owned("sources", record["source"]["id"], actor)
            if source["revision"] != record["source"]["revision"]:
                raise ValueError("原始材料已经修改，请重新提出候选")
            context = {"purpose": "resource", "source": {k: source[k] for k in ("id", "revision", "text")},
                       "catalog": [d for d in self.catalog(actor) if d["entity_type"] == "Service"]}
        elif record["state"] == "drafting":
            context = {"purpose": "task", "goal": record["goal"], "catalog": self.catalog(actor), "tools": self.tools(actor)}
        else:
            context = {"purpose": "query", "conditions": record["conditions"], "answer": record.get("answer", ""),
                "catalog": self.catalog(actor), "tools": self.tools(actor), "remaining_steps": MAX_STEPS-record["attempts"],
                "history": record["history"]}
        return record, context

    def pending(self, record: dict, value: dict) -> None:
        record.update(state="needs_confirmation", pending=value, confirmation_hash=digest(value))

    def apply(self, payload: dict, actor, decision: dict | None, provider: dict, failure: str | None = None) -> dict:
        record, context = self.prepare(payload, actor)
        record["attempts"] += 1
        record["provider"] = provider
        entry = {"step": record["attempts"], "purpose": context["purpose"], "at": self.w.now().isoformat(),
                 "provider": provider, "decision": deepcopy(decision)}
        try:
            if failure:
                raise ValueError(failure)
            if context["purpose"] == "task":
                exact(decision, {"goal", "scope", "completion", "questions"})
                conditions = {k: text(decision[k], k) for k in ("goal", "scope", "completion")}
                self.pending(record, {"conditions": conditions, "questions": strings(decision["questions"], "澄清问题")})
            elif context["purpose"] == "resource":
                candidate = self.resource_candidate(decision, record, actor)
                release = {"source": deepcopy(record["source"]), "candidate": candidate}
                preview = self.w._build(extra_release=release)
                record.update(state="needs_review", candidate=candidate, validation=preview.model_validation,
                    confirmation_hash=digest(release), preview_manifest=preview.manifest)
            else:
                entry["result"] = self.query_step(record, decision, actor)
        except (ValueError, KeyError, TypeError) as error:
            entry["error"] = str(error) if isinstance(error, ValueError) else "模型字段或类型不符合约定"
        record["history"].append(entry)
        if record["attempts"] >= MAX_STEPS and record["state"] in ("ready", "drafting"):
            record["state"] = "budget_exhausted"
        return self.public(record)

    def resource_candidate(self, decision: dict, record: dict, actor) -> dict:
        exact(decision, {"title", "entity_type", "type_description", "question", "quote", "links"})
        result = {k: text(decision[k], k, 6000 if k == "quote" else 500)
                  for k in ("title", "entity_type", "type_description", "question", "quote")}
        kind = result["entity_type"]
        if not re.fullmatch(r"[A-Z][A-Za-z]{2,39}", kind):
            raise ValueError("候选类型名必须是3—40个英文字母")
        if kind in self.w.platform.domain_model["entityTypes"] and kind not in ("Runbook", "ADR"):
            prior = [r for r in self.state["releases"] if r["source"]["id"] == record["source"]["id"]
                     and r["candidate"]["entity_type"] == kind]
            if not prior:
                raise ValueError("不得覆盖已有类型；请复用 Runbook、ADR 或提出新类型")
        if result["quote"] not in record["source"]["text"]:
            raise ValueError("候选引用没有逐字出现在原文中")
        links = decision["links"]
        if not isinstance(links, list) or not 1 <= len(links) <= 4:
            raise ValueError("至少提出一条、最多四条有出处的服务关系")
        visible = {x["id"] for x in self.catalog(actor) if x["entity_type"] == "Service"}
        seen = set()
        result["links"] = []
        for link in links:
            exact(link, {"from", "quote"})
            identity = text(link["from"], "服务ID", 100)
            quote = text(link["quote"], "关系引文", 6000)
            if identity not in visible or identity in seen or quote not in record["source"]["text"]:
                raise ValueError("关系端点不可用、重复或缺少原文引用")
            seen.add(identity)
            result["links"].append({"from": identity, "quote": quote})
        return result

    def query_step(self, record: dict, decision: dict, actor) -> dict:
        exact(decision, {"action", "args", "reason"})
        text(decision["reason"], "取证理由", 1000)
        action, args = decision["action"], decision["args"]
        if action not in self.tools(actor):
            raise ValueError("该角色没有这个取证工具；模型不能增加能力")
        keys = {"search": {"question"}, "trace": {"seed"}, "wiki": set(), "observe": {"resource"},
                "metric": set(), "clarify": {"question"}, "finish": {"summary", "missing"}}
        exact(args, keys[action])
        p = self.w.platform
        flow = ContextFlow(p)
        if action == "clarify":
            self.pending(record, {"question": text(args["question"], "澄清问题")})
            return {"status": "needs_confirmation"}
        if action == "finish":
            summary = text(args["summary"], "材料说明")
            missing = strings(args["missing"], "缺口")
            reads = [e for e in record["history"] if e.get("result") is not None and
                     e.get("decision", {}).get("action") in ("search", "trace", "wiki", "observe", "metric")]
            if not reads:
                raise ValueError("至少执行一次取证后才能交付上下文")
            package = {"request_id": record["id"], "principal": asdict(actor), "manifest": p.manifest,
                "task_conditions": deepcopy(record["conditions"]), "captured_at": self.w.now().isoformat(),
                "interpretation": {"text": summary, "status": "model_proposal_needs_review"},
                "materials": [{"tool": e["decision"]["action"], "step": e["step"], "result": deepcopy(e["result"])} for e in reads],
                "missing": missing, "allowed_tools": self.tools(actor), "business_task_completed": False}
            # Re-check short-lived observations at handoff, not only at collection.
            for item in package["materials"]:
                if item["tool"] == "observe":
                    current = p.get_status("refund-queue", actor)
                    if current is None or current != item["result"].get("observation"):
                        item["result"] = {"observation": None, "missing": ["队列观察已过期或发生变化"]}
                        package["missing"].append("队列观察已过期或发生变化，需要重新读取")
            record.update(state="ready_for_review", package=package)
            record["snapshots"].append(deepcopy(package))
            return {"status": "ready_for_review", "note": "已交付材料，业务任务尚未宣告完成"}
        if action == "search":
            result = flow.read("search", {"question": text(args["question"], "检索问题")}, actor)
            return {"evidence": result["evidence"][:8]}
        if action == "trace":
            seed = text(args["seed"], "起点ID", 150)
            if seed not in {x["id"] for x in self.catalog(actor)}:
                raise ValueError("起点不可用")
            return flow.read("trace", {"seed": seed}, actor)
        if action == "wiki":
            return flow.read("wiki", {}, actor)
        if action == "observe":
            if args["resource"] != "refund-queue":
                raise ValueError("本例只有 refund-queue 观察入口")
            readings = flow.read("observe", {"resource": "refund-queue"}, actor)["observations"]
            observation = readings[0] if readings else None
            return {"observation": observation, "missing": [] if observation else ["队列观察不可用或已过期"]}
        result = flow.read("metric", {"question": record["conditions"]["goal"],
                           "confirmation": record.get("metric_confirmation")}, actor)
        if result.get("status") == "needs_clarification":
            self.pending(record, {"metric_contract": p.strategy_context.definition_confirmation(),
                                  "question": "请核对完整的指标、期间、范围和版本；只支持这份教学契约。"})
        return result
