# 第 16 章 加入 Wiki、关系图与记忆

可信检索能找到政策、代码和 Runbook，却仍要求调用者自己重建系统全貌。Northstar 的下一阶段增加三种派生能力：Wiki 把重复理解编译成页面，关系图连接跨仓与跨来源对象，任务记忆让事故调查跨会话延续。三者共同使用第 11 章的对象信封和血缘，不建立新的事实孤岛。

本章仍遵循一个原则：先确定任务与可验证关系，再生成页面和图。批量生成数百篇摘要很容易，证明它们在变更后仍然正确、权限一致并能回到源码则困难得多。

## 16.1 建立确定性骨架

Northstar 从无需模型推断的来源建图。服务目录给出服务与团队，OpenAPI 给出服务与接口，事件 Schema 给出事件与版本，代码解析给出仓库、文件、符号和显式调用，测试清单给出被测对象，Runbook frontmatter 给出适用系统。

最小节点类型包括 `BusinessCapability`、`Service`、`Repository`、`Symbol`、`API`、`Event`、`Runbook`、`Test`、`Team` 和 `Incident`。最小关系包括 `OWNS`、`IMPLEMENTS`、`CALLS`、`PRODUCES`、`CONSUMES`、`TESTED_BY`、`DOCUMENTED_BY` 和 `AFFECTED_IN`。

边记录来源和证据等级。例如 OpenAPI operation 到处理函数的映射若由明确注解解析，可标记 `resolved`；仅凭相同名称连接则是 `heuristic`。模型从事故叙述中抽取“部署可能导致积压”只能标为 `inferred`，直到部署记录和指标验证。

一个简化边对象如下：

```json
{
  "from": "event:order.cancelled@v2",
  "type": "CONSUMED_BY",
  "to": "symbol:payment#handle_order_cancelled",
  "evidence": "code://northstar/payment@c1/handlers.py#handle_order_cancelled",
  "evidence_tier": "resolved",
  "valid_from": "2026-07-11T00:00:00Z"
}
```

图构建测试验证外键、唯一实体、允许边类型和证据 URI。任何无法解析的目标保留为 unresolved report，而不是悄悄创建同名节点。

## 16.2 代码仓是子图，不是文档文件夹

每个逻辑仓形成一个子图：仓库包含文件，文件定义符号，符号调用符号、实现 API 或消费事件，测试覆盖符号。仓间通过事件、API、包和部署产物连接。这个结构允许 `order.cancelled` 从 Schema 节点同时扩展到 Payment、Inventory 和 Notification，而不依赖三份文档使用相同措辞。

Tree-sitter 用于恢复语法结构和候选调用，语言级索引或编译器信息用于精确符号关系。案例源码很小，可以用 Python AST 或规则解析；书中保持接口为 `nodes.jsonl` 与 `edges.jsonl`，使解析器可替换。

ArtifactFS 保存固定提交的源码，图只保存引用和结构属性。查询最后总能回到 `code://...@commit/path#symbol`，而不是把图数据库中的摘要当作代码事实。仓库更新时创建新符号版本，未变化对象可复用内容散列。

## 16.3 从叶子编译分层 Wiki

Northstar 定义四层页面：业务流程、系统、仓库和模块/符号。业务流程页解释订单取消的规则与参与系统；系统页解释 Payment Service 的职责、接口、依赖和运行方式；仓库页给出构建、目录、入口和测试；模块页解释关键实现并链接源码。

页面生成分两阶段。第一阶段使用确定性模板填入实体、关系、所有者和引用；第二阶段可选用模型把证据综合成叙述。没有模型时，模板页面仍完整可导航。模型输出必须通过结构解析和声明引用检查。

页面清单保存：

```yaml
page_id: wiki:system:payment
schema: system-page@1
inputs:
  - service:payment@v1
  - repo:payment@c1
  - runbook:refund-backlog@v2
generator: template@1
review: approved
freshness: ready
acl_policy_id: acl:engineering
```

客服域另行生成不含源码与内部 Runbook 的业务页面。平台不会先生成工程页面再删字段，因为剩余叙述可能泄露内部结构。页面安全域属于生成输入。

## 16.4 页面内容如何保持可核验

模板中的事实字段直接绑定对象或边。模型生成的每个段落则返回声明列表与证据 ID。Lint 检查引用可解析、输入版本属于同一 Manifest、关键字段非空、没有越权来源和孤立声明。

若页面写“所有订单取消都会触发退款”，政策却说明未支付订单不触发，声明验证应失败或把例外补入上下文。摘要目标不是最短，而是在目标抽象层保留决定性条件。

页面审核状态分为 `draft`、`reviewed` 和 `approved`。低风险代码导览可以自动发布为 draft，高风险处置步骤只有 approved 才能作为行动证据。检索结果显示状态，Agent 规划时按风险过滤。

## 16.5 增量失效

来源 diff 首先更新叶子对象和确定边，再通过依赖图传播。`order.cancelled` Schema 新增字段时，事件节点创建新版本，消费者边进入待验证，对应符号与测试页面标 stale，三个仓库页和业务流程页进入重建队列。

传播规则按变更类型设置。注释变化可能只影响符号摘要；接口签名变化影响调用者、测试和系统页；ACL 变化立即撤销所有派生页面；模型或提示升级只使相应生成物重建，不改变确定图。

流水线把连续提交合并到同一目标快照，避免每次提交重复生成上层页面。失败页面保持上一已发布版本，但响应标注其覆盖快照；若来源撤销或安全变化，则不能继续服务旧页面。

## 16.6 为退款积压建立任务记忆

事故任务以 `incident_id` 作为记忆主体。状态对象包括目标、负责人、时间线、已检查指标、排除假设、证据、已执行只读查询、待确认动作和下一步。每次更新使用版本和乐观并发，防止两个 Agent 覆盖彼此进度。

一条任务事件可以是：

```json
{
  "incident_id": "INC-1042",
  "type": "hypothesis_rejected",
  "statement": "支付网关错误率不是主要原因",
  "evidence": ["runtime://northstar/payment/error-rate@2026-08-23T10:05Z"],
  "actor": "user:alice",
  "created_at": "2026-08-23T10:06Z"
}
```

任务恢复时，系统返回当前摘要与未完成步骤，而不是重放全部聊天。实时指标过期后只保留历史观察，不作为当前状态。用户纠错追加替代关系，原错误仍保留用于审计但停止召回。

## 16.7 从事故经验到知识候选

事故关闭后，系统编译一份结果：根因、证据、有效处置、无效尝试、适用版本和建议更新。它首先是 `knowledge_candidate`，不自动进入公共 Wiki。Runbook 所有者审核后，分别更新正式手册、代码注释或监控规则。

晋升后的知识链接原事故和审核记录。若同类事故再次发生，平台可以比较环境与版本，而不是无条件复制旧动作。未通过审核的候选按保留期归档，避免组织知识队列无限膨胀。

这条流程使记忆承担“保存工作经验”，Wiki 承担“发布稳定解释”，规范来源承担“定义规则”。三者有流动，但没有混为一体。

## 16.8 用影响题验证组合能力

Golden Question “修改 `order.cancelled` 会影响什么”首先由 BM25 或向量命中事件页面；图沿 `CONSUMED_BY` 找到三个处理符号，沿仓库层级找到三个仓，沿 `TESTED_BY` 和 `DOCUMENTED_BY` 找到测试与 Runbook；Wiki 提供业务流程摘要；最终引用回到 Schema 和源码。

评测分别检查必要节点召回、边证据、页面声明和源码引用。去掉图后，文本检索可能漏掉命名不同的消费者；去掉 Wiki 后，证据仍在但缺少高层解释；去掉源码 ArtifactFS 后，图路径无法最终核验。消融清楚展示每层的贡献。

权限矩阵再次运行：客服只能得到取消流程和政策，不得到仓库图；开发者得到代码影响；负责人还看到相关事故任务。图和 Wiki 不能绕过第 15 章的对象过滤。

## 本章小结

Northstar 先以服务目录、Schema、源码和测试建立确定性图骨架，再让模型推断补充语义。代码仓作为子图通过事件和 API 连接，分层 Wiki 则把图与来源编译成不同安全域的阅读视图。变更从叶子沿血缘增量失效，任务记忆保存事故工作但不自动晋升为组织知识。三种能力的共同价值，是让检索结果能够在抽象层之间导航并持续更新，而不是生成更多页面。

## 延伸阅读

- Tree-sitter, [Documentation](https://tree-sitter.github.io/tree-sitter/)。
- SCIP contributors, [SCIP](https://github.com/scip-code/scip)。
- W3C, [PROV-O](https://www.w3.org/TR/prov-o/)。
