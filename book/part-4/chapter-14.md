# 第 14 章 案例企业与需求设计

> 本章要回答：如何把真实工作任务转化为可运行、可验收的企业上下文案例？

这一章开始构建 Northstar Commerce 企业上下文系统。案例不是对某个商业产品的演示，而是一条可以替换组件的参考实现：先用小型、确定的数据证明对象、权限、版本、检索与评测契约，再逐步加入向量、图、Wiki、记忆和工具。

Northstar 是虚构在线零售企业，避免公开案例依赖真实公司的机密数据。它仍保留生产问题的主要复杂性：多个服务和代码仓、地区政策、历史架构决策、运行手册、事故、角色权限、实时状态和高风险动作。

## 14.1 企业与系统边界

Northstar 的订单域包含五个逻辑服务。Order Service 管理订单状态；Payment Service 负责支付授权与退款；Inventory Service 预留和释放库存；Fulfillment Service 处理出库；Notification Service 发送客户消息。事件总线连接这些服务，`order.cancelled` 会触发退款、库存释放和通知。

案例聚焦两个任务链。第一条是订单取消：解释规则、追踪事件消费者并分析 Schema 变化影响。第二条是退款积压：读取当前指标，结合 Runbook、部署、代码和历史事故形成诊断，并在需要重放消息时进入审批工具。

范围刻意不包括完整电商实现、真实支付网关和模型托管。业务 API 使用本地 fixture，代码仓使用小型逻辑仓，语义检索有可选本地模式。这样读者可以在普通开发机上重建核心链路，再按章节建议替换为 PostgreSQL、pgvector、图数据库和实际模型。

## 14.2 数据集不是文档堆，而是任务世界

一个有用的样例数据集应包含互相引用、会发生冲突且拥有不同权限的来源。Northstar 规划以下材料：

- 五个逻辑代码仓及构建、测试和提交版本；
- 产品规则、地区退款政策与订单状态机；
- 6—10 份架构决策记录（ADR）；
- 8—12 份 Runbook、事故复盘和工单；
- OpenAPI、事件 Schema、部署与监控配置；
- 服务目录、团队所有权与值班信息；
- 企业架构能力图、流程模型与应用依赖声明；
- 脱敏订单、队列指标和任务历史 fixture；
- 客服、开发者、值班负责人等角色及 ACL；
- 24 条教学用 Golden Questions 和必要或禁止证据；生产评测集需要在真实查询分布上继续扩充。

原始来源保持人工可读，使用 Markdown、JSON、YAML 和小型源码。生成的分块、索引、图和 Wiki 不手工维护，可以从来源重建。这个边界让读者看见平台到底增加了什么，也能验证删除来源后派生物是否消失。

## 14.3 从任务写需求

第一步不是选择向量数据库，而是写清智能体要完成的工作。案例选择七类验收任务：

1. 解释订单取消流程，并区分业务规则与代码实现；
2. 修改 `order.cancelled` 事件时，找出仓库、消费者、测试和 Runbook；
3. 退款积压告警发生时，形成有证据的排查计划；
4. 当前政策与历史 ADR 冲突时，按时间和权威来源判断；
5. 说明每项结论来自源码、文档、实时工具还是模型推断；
6. 证明客服、开发者、负责人和跨租户用户获得不同证据与行动权限。
7. 比较企业架构声明、代码解析和运行观察，识别一致关系与待核验差异。

每项任务都可以被测试。比如影响分析不是“回答看起来完整”，而是必须包含 Payment、Inventory、Notification 三个消费者及对应测试；客服查询不能出现代码对象；历史政策题必须选择指定业务时间有效版本。

需求还包括非功能约束：本地可运行、无商业 API 也能降级、摄取幂等、引用可回跳、查询可重放、权限失败关闭、组件失败透明降级、固定依赖以及测试数据不包含秘密。

## 14.4 角色与权限矩阵

案例使用四类主体。`support` 可读公开产品规则、客服政策和自己租户的订单状态；`developer` 还可读代码、ADR 和工程 Runbook；`incident_commander` 可以读取生产指标并准备受控动作；`external` 只访问公开说明。另设第二租户验证隔离。

权限矩阵按对象类型与具体对象结合。代码默认仅工程角色可见，安全事故 Runbook 可能进一步限制；订单工具执行行级租户过滤；派生 Wiki 按安全域生成。角色只是示例，真实企业可接入组、属性和策略引擎。

测试使用正反成对样本：开发者应找到退款代码，客服以同一查询不得召回；客服能查租户 A 的订单，切换到租户 B 必须拒绝；负责人可以获取动作预览，但未确认不得执行。

## 14.5 统一 URI 与对象清单

知识对象采用稳定逻辑 URI：

```text
knowledge://northstar/{kind}/{object-id}@{version}#{locator}
code://northstar/{repository}@{commit}/{path}#{symbol}
runtime://northstar/{system}/{resource}@{observed-at}
memory://northstar/{subject}/{memory-id}@{version}
```

URI 不是要求所有后端理解自定义协议，而是案例内部的规范引用。对象清单把 URI 映射到来源路径、内容散列、ACL、有效时间和派生状态。稳定逻辑 ID 用于跨版本关系，带 `@version` 的 URI 用于证据。

例如政策条款的逻辑对象是 `knowledge://northstar/policy/refund-window`，当前证据可能是 `@v3#emea`；代码引用包含 Git 提交，因此即使主分支变化也能重放。实时 URI 使用观察时间，不伪装成永久事实。

## 14.6 Golden Questions 如何标注

每条金标准样本保存结构化字段：

以下是生产题集的完整字段设计。配套教学题集 `data/golden-questions.json`（亦见附录 D.1）只实现可执行的行为断言，并不实现完整证据契约：`query` 对应 `question`，`principal.role` 对应 `role`；`expected_ids` 只断言结果中应出现哪些对象 ID，不能等同于 `required_evidence`。负结果、缺失资源和动作约束分别由 `forbidden_ids`、`expected_missing`、`forbidden_tools` 或 `expected_tool` 表示。教学子集没有独立的 `snapshot`、规范证据 URI 或标准答案文本；历史时间条件目前保留在题目文本及对应 fixture 中。

```json
{
  "id": "GQ-IMPACT-001",
  "principal": {"role": "developer", "tenant": "northstar"},
  "query": "修改 order.cancelled 会影响什么？",
  "snapshot": "northstar-v1",
  "required_evidence": [
    "code://northstar/payment@c1/handlers.py#on_order_cancelled",
    "code://northstar/inventory@c1/events.py#release_reservation",
    "code://northstar/notification@c1/consumer.py#send_cancelled"
  ],
  "forbidden_evidence": [],
  "required_relations": ["CONSUMED_BY", "TESTED_BY"],
  "expected_action": "none"
}
```

问题集按精确定位、语义解释、跨来源综合、关系影响、历史时间、权限隔离、拒答、提示注入和行动审批分桶。每个桶保留简单与困难样本。标注者首先确定证据，再写可接受答案范围；这样模型措辞变化不会频繁破坏测试。

数据集也保存负证据。若问题缺少订单 ID，应要求澄清而不是猜测；若运行指标工具离线，应声明无法判断当前积压；若两个低权威来源冲突，应返回冲突而不是选一条。正确失败是平台能力的一部分。

## 14.7 参考实现目录

完整案例采用清晰分层：

```text
examples/enterprise-case/
├── data/                 # 原始来源、EA 声明与角色策略
├── fixtures/             # 实时系统与任务事件
├── src/                  # 摄取、索引、图、API和工具
├── generated/            # 可删除并重建的索引与Wiki
├── tests/                # 单元、集成、安全和Golden测试
├── docker-compose.yml    # 可选完整基础设施
└── README.md             # 从零复现步骤
```

本书当前的最小纵向切片使用 `knowledge.json` 和无依赖 Python BM25，先证明 ACL、版本化引用和角色差异。后续章节在不改变外部对象契约的前提下增加索引、图、Wiki 和 Context API。读者可以在任一阶段运行测试，而不是到最后才发现基础身份模型错误。

## 14.8 分阶段验收

阶段一验收对象、ACL 和引用；阶段二验收 BM25、向量与融合；阶段三验收 Wiki 血缘、图路径与架构一致性；阶段四验收任务记忆与 Context API；阶段五验收工具审批、可观测性和完整任务。

每个阶段都包含可重建性检查：删除 `generated/`，从固定来源重新运行，得到语义等价产物；包含安全检查：同一问题运行角色矩阵；包含回归检查：所有旧 Golden Questions 继续通过。新能力只有在对应题型产生可测收益后才保留。

最小成功标准始终不变：召回前鉴权、不可变版本引用、查询可重放、证据不足可拒答。向量、图和模型生成可以增强质量，却不能代替这些契约。

## 本章小结

Northstar 把企业上下文问题缩小为两条真实任务链，并用代码、规则、决策、运行资料、实时 fixture 与角色权限构成一个可测试世界。需求从工作任务和失败条件出发，Golden Questions 同时标注身份、快照、必要与禁止证据。统一 URI 把所有投影连接到版本化来源，分阶段实现则确保每增加一层复杂度都能被验证。下一章从最小证据检索开始动手。

## 延伸阅读

- Patrick Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401), 2020。
- Microsoft Research, [GraphRAG documentation](https://microsoft.github.io/graphrag/)。
- OWASP, [Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)。
- OpenTelemetry, [Tracing](https://opentelemetry.io/docs/concepts/signals/traces/)。
- Model Context Protocol, [Specification](https://modelcontextprotocol.io/specification/)。
