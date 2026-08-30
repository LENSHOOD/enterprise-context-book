# Northstar Commerce 可复现纵向切片

该原型使用 Python 标准库验证书中的核心契约：召回前 ACL、版本化引用、BM25 与离线语义代理通道融合、受权限约束的关系遍历、企业架构声明与实现/运行证据的差异检测、带血缘的 Wiki、任务记忆、实时观察、结构化 Context Package 和最小受控动作闭环。它是本地降级实现，不冒充大规模生产检索；数据库、嵌入模型和图后端可以在保持接口与测试的前提下替换。

```bash
python3 src/northstar.py "修改 order.cancelled 会影响什么" \
  --role developer --graph-seed event-order-cancelled
python3 src/northstar.py "退款积压如何排查" \
  --role incident_commander --runtime-resource refund-queue --task INC-1042
python3 src/northstar.py --architecture-consistency --role developer
python3 src/action_demo.py
python3 -m unittest discover -s tests -v
```

`context_demo.py` 保留为第 15 章最小 BM25 基线；`northstar.py` 是完成后的纵向切片。所有数据位于 `data/`，无网络、模型密钥或外部数据库要求。

`data/domain-model.json` 是第 8 章的机器可读领域模型。它从能力问题出发，定义实体身份、关系方向与基数、允许的证据等级、时间约束和源映射；`knowledge.json`、`relations.json` 等运行数据可以视为该逻辑模型的简化物理投影。`architecture-claims.json` 保存 EA 应用视图中的 `asserted` 关系，`NorthstarPlatform.architecture_consistency()` 将它们与 `resolved`/`observed` 证据比较。示例刻意不要求 RDF 或图数据库，以说明知识建模与具体存储可以解耦。

Northstar、commit、业务事件及其日期均为合成 fixture。`time.valid_from` 表示示例业务生效时间，`time.observed_at` 表示教学系统摄取时间；两者不再用同一“写文件日期”代填。`NorthstarPlatform.documents_as_of` 演示双轴过滤，但只保存首次观察时间，精确历史重放仍需使用当时发布的不可变 Manifest。

Docker Compose 一键验证：

```bash
docker compose up --build --abort-on-container-exit verify
docker compose --profile query run --rm query
```

容器禁用网络、使用只读文件系统，并固定 Python 3.12.5 的镜像 manifest 摘要。升级基础镜像时应重新构建并运行全部测试。

实现边界：离线语义代理使用确定性同义词扩展与 Jaccard 相似度，不是向量检索；生产部署应替换为经过企业题集评测的嵌入模型。任务记忆和重放队列都是进程内 fixture，用于证明主体隔离、审批、幂等和验证契约；持久化版本应使用带版本控制和删除策略的数据库与真实工具网关。
