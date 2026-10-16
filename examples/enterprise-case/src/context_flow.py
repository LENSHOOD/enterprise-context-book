"""Shared context plan, read executor and package assembly; no web/session code."""
from copy import deepcopy
from dataclasses import asdict
from time import perf_counter

from modeling import semantic_slice
from context_delivery import deliver, sales_documents
from refund_records import read_records


class ContextFlow:
    def __init__(self, platform):
        self.platform = platform

    def plan(self, question, *, mode="operational", graph_seed=None, runtime_resource=None,
             disabled_channels=None, competency_question_id=None, valid_at=None, observed_at=None,
             definition_confirmation=None):
        """Turn explicit caller choices into a plan; this is not an LLM planner."""
        if mode not in ("operational", "strategic"):
            raise ValueError(f"unknown context mode {mode}")
        if mode == "strategic" and any((graph_seed, runtime_resource, disabled_channels,
                                        competency_question_id, valid_at, observed_at)):
            raise ValueError("strategic mode uses its explicit fixed-snapshot contract")
        competency = self.platform.competency_question(competency_question_id) if competency_question_id else None
        if mode == "strategic":
            steps = [{"tool": "metric", "args": {"question": question,
                       "confirmation": deepcopy(definition_confirmation)},
                      "purpose": "确认口径，读取企业背景并计算同口径差异"}]
        else:
            steps = [{"tool": "search", "args": {"question": question,
                       "disabled_channels": sorted(disabled_channels or []),
                       "valid_at": valid_at, "observed_at": observed_at}, "purpose": "找到可引用的材料"}]
            if graph_seed:
                steps.append({"tool": "trace", "args": {"seed": graph_seed,
                              "relation_types": competency["requiredRelations"] if competency else None,
                              "allow_inverse_navigation": competency is not None,
                              "valid_at": valid_at, "observed_at": observed_at}, "purpose": "查清对象关系和影响路径"})
            if runtime_resource:
                steps.append({"tool": "observe", "args": {"resource": runtime_resource}, "purpose": "核对当前状态"})
        return {"mode": mode, "question": question, "steps": steps, "competency_question": competency}

    def read(self, tool, args, principal):
        """Run a read through the platform's existing permission and time checks."""
        p = self.platform
        if tool == "search":
            return {"evidence": p.search(args["question"], principal, limit=args.get("limit", 5),
                    disabled_channels=set(args.get("disabled_channels", [])),
                    valid_at=args.get("valid_at"), observed_at=args.get("observed_at"))}
        if tool == "trace":
            types = args.get("relation_types")
            return {"relations": p.trace(args["seed"], principal,
                    max_hops=args.get("max_hops", 2),
                    relation_types=set(types) if types is not None else None,
                    allow_inverse_navigation=args.get("allow_inverse_navigation", False),
                    valid_at=args.get("valid_at"), observed_at=args.get("observed_at"))}
        if tool == "lookup":
            requested = set(args["ids"])
            docs = p.current_documents(principal, valid_at=args.get("valid_at"),
                                       observed_at=args.get("observed_at"))
            return {"evidence": [p._hit(doc, 1.0, ["lookup"]) for doc in docs
                                 if doc["id"] in requested]}
        if tool == "wiki":
            return {"wiki": p.build_wiki(principal)}
        if tool == "observe":
            observation = p.get_status(args["resource"], principal)
            return {"observations": [observation] if observation else [],
                    "missing": [] if observation else [args["resource"]]}
        if tool == "metric":
            catalog = {doc["id"]: doc for doc in sales_documents(p, principal)}
            if not set(p.strategy_context.by_id) <= set(catalog):
                # The fixed aggregate exposes the entire snapshot; a partially
                # authorized snapshot cannot safely produce that aggregate.
                raise PermissionError("当前身份不能读取完整的销售快照")
            result = p.strategy_context.package(args["question"], asdict(principal),
                                                confirmation=args.get("confirmation"))
            for item in result.get("evidence", []):
                item["version"] = catalog[item["id"]]["version"]
            return result
        if tool == "business":
            return read_records(p, principal)
        raise ValueError("unknown context read tool")

    def assemble(self, plan, results, principal, task_id):
        p = self.platform
        memories = p.memory.read(task_id, principal)
        package = {"trace_id": f"ctx:{principal.tenant}:{task_id}:{len(memories) + 1}",
                   "manifest": p.manifest, "principal": asdict(principal), "task_id": task_id,
                   "context_kind": plan["mode"], "query_plan": deepcopy(plan["steps"]),
                   "evidence": [], "relations": [], "observations": [], "memories": memories,
                   "missing": [], "degraded_channels": [], "allowed_tools": [], "task_state": "opened"}
        for result in results:
            for key, value in result.items():
                if key in ("evidence", "relations", "observations", "missing"):
                    package[key].extend(deepcopy(value))
                else:
                    package[key] = deepcopy(value)
        if plan["mode"] == "operational":
            package["semantic_contract"] = semantic_slice(p.domain_model,
                [p.by_id[item["id"]] for item in package["evidence"]], package["relations"],
                competency_question=plan["competency_question"])
            package["degraded_channels"] = next((s["args"].get("disabled_channels", []) for s in plan["steps"] if s["tool"] == "search"), [])
            package["allowed_tools"] = p.allowed_tools(principal, task_id)
            package["task_state"] = p.task_state(task_id, principal)
        return deliver(package, conditions={"goal": plan.get("question", "本轮上下文调查"),
                                            "scope": plan["mode"]})

    def execute(self, plan, principal, task_id):
        """Execute a server-authored plan with dependent reads and measured output."""
        results = []
        executed, measurements = [], []
        for step in plan["steps"]:
            args = deepcopy(step["args"])
            if "relations_from" in step:
                edges = results[step["relations_from"]].get("relations", [])
                args["ids"] = sorted(set(args.get("ids", [])) |
                                     {edge[end] for edge in edges for end in ("from", "to")})
            started = perf_counter()
            result = self.read(step["tool"], args, principal)
            elapsed_ms = round((perf_counter() - started) * 1000, 3)
            executed.append({"tool": step["tool"], "args": args, "purpose": step["purpose"]})
            measurements.append({"tool": step["tool"], "elapsed_ms": elapsed_ms,
                "returned_items": sum(len(result.get(key, [])) for key in
                                      ("evidence", "relations", "observations")),
                "evidence_chars": sum(len(item.get("evidence", ""))
                                      for item in result.get("evidence", []))})
            results.append(result)
            if result.get("status") == "needs_clarification":
                break
        package = self.assemble({**plan, "steps": executed}, results, principal, task_id)
        package["execution_report"] = {"tool_calls": len(executed), "steps": measurements,
            "elapsed_ms": round(sum(item["elapsed_ms"] for item in measurements), 3),
            "returned_items": sum(item["returned_items"] for item in measurements),
            "evidence_chars": sum(item["evidence_chars"] for item in measurements)}
        return deliver(package)

    def run(self, question, principal, task_id, **choices):
        return self.execute(self.plan(question, **choices), principal, task_id)
