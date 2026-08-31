# 第 16 章 C3：让对象形成图、Wiki 与可持续经验

> 本章要回答：在已经可信的对象上，如何加入关系、解释和记忆，而不制造新的事实孤岛？

C1 和 C2 的检索结果仍然是一组候选对象。开发者看到 `order.cancelled`、三个代码消费者和三个测试时，仍要自己拼出“修改事件会影响什么”。C3 的目标是把这种重复拼接变成可导航、可核验、可失效的派生视图，同时保证图、Wiki 和任务记忆都不绕过已经建立的权限与版本边界。

## 16.1 C3 的输入和输出

**新增输入**：扩展教学 fixture 中的 `data/relations.json`、`data/domain-model.json`、`data/architecture-claims.json` 与运行观察。**新增代码**：`src/knowledge_views.py`。它只接收已经可见的对象 ID、边或架构声明，不直接读取数据文件，也不自行决定谁有权限。

```bash
cd examples/enterprise-case
python3 src/northstar.py "修改 order.cancelled 会影响什么" \
  --role developer --graph-seed event-order-cancelled
```

读者应该在 `relations` 中看到三条 `CONSUMED_BY` 边，再沿每个消费者看到 `TESTED_BY` 边。若将相同命令换为 `--role support`，起点事件本身对该角色不可见，遍历结果是空数组。这个空结果比“只隐藏末端代码节点”更重要：它证明权限边界在图构建前就已经生效。

## 16.2 先让关系有可检查的含义

图数据库不自动带来知识模型。Northstar 的关系类型、主客体类型、时间性和可接受证据等级集中定义在 `data/domain-model.json`。例如：

```json
{
  "CONSUMED_BY": {
    "from": "EventSchema",
    "to": "CodeSymbol",
    "cardinality": "one_to_many",
    "allowedEvidence": ["deterministic", "resolved"],
    "temporal": true
  }
}
```

而实例边必须带能回跳的证据：

```json
{
  "from": "event-order-cancelled",
  "type": "CONSUMED_BY",
  "to": "code-refund-consumer",
  "evidence_tier": "resolved",
  "evidence": "code://northstar/refund-worker@abc123/consumer.py#handle_order_cancelled"
}
```

这两层缺一不可。只存边而没有关系契约，会把“服务调用 API”“事件被代码消费”“团队值班”混成同一种连接；只有模型而没有实例与证据，则无法回答任何能力问题。`test_domain_model.py` 同时检查关系约束、实例边、时间约束和每个对象的治理信封。

## 16.3 C3：在授权集合内遍历图

`knowledge_views.trace_dependency()` 的输入是 `edges`、`visible_ids`、起点和最大跳数。它的第一步不是搜索，而是限制邻接表：

```python
for edge in edges:
    if edge["from"] in visible_ids and edge["to"] in visible_ids:
        adjacency[edge["from"]].append(edge)
```

随后才执行有界广度优先遍历。图查询的“可见性”不是在最终路径上打码，而是无权节点和边根本不进入邻接表。生产系统可以把这一步下推到图数据库、按安全域分图，或在网关做策略编译；无论选择何种后端，测试应验证同一条路径不能跨过 ACL。

每个代码仓在概念上是子图：仓包含文件，文件定义符号，符号消费事件、调用 API，测试覆盖符号。仓间通过事件、API、包和部署产物连接。Northstar 的教学 fixture 只实现三个消费者和一个仓对象，正是为了让读者清楚看见子图与跨图连接的区别；它不声称已经对真实仓库运行 Tree-sitter 或 SCIP。

### 从教学数据到真实代码索引

在生产系统中，Tree-sitter 可提供文件、符号和候选调用，语言索引或编译信息可提高符号关系确定性，SCIP 或 LSP 可提供跨编辑器导航。不同证据等级必须保留：语法候选不能伪装成编译级调用，运行追踪也不能被当成代码的完整静态证明。最终证据仍应回到 ArtifactFS 中固定提交的源码引用，详见[第 18 章](/part-5/chapter-18)。

## 16.4 C3：编译不泄露的 Wiki

图让系统能导航，Wiki 让人能从合适的抽象层开始理解。运行以下命令：

```bash
python3 src/northstar.py --wiki --role support
python3 src/northstar.py --wiki --role developer
```

两个输出都是确定性页面列表。每页的 `inputs` 是本页使用的版本化引用，因此既是血缘，也让页面可以在输入变化时失效。support 页面只包含政策、退款事件和团队信息；developer 页面可以包含代码与工程资料。平台不会先生成工程页面再从文本中删字段，因为剩余描述可能仍泄露仓、符号或内部处置步骤。

`knowledge_views.build_role_scoped_wiki()` 的实现保持简单：按系统分组可见对象，使用模板写入标题、摘要和引用。这是有意选择。没有模型时，读者仍能检查页面输入和 ACL；生产系统可以在模板之后调用模型生成叙述，但每个声明都必须返回引用并通过 Schema、权限和事实检查。

一个可靠 Wiki 至少需要以下发布规则：

1. 输入对象属于同一已发布 Snapshot Manifest；
2. 每个关键字段可回到对象或边证据；
3. 页面按安全域分别生成；
4. 来源变更、ACL 变更或模型提示升级会使相关页面 stale；
5. 高风险处置页要经过人工审核，不能仅因模型生成成功而作为行动依据。

## 16.5 C3：将企业架构声明接入运行反馈

企业架构图不是“永远正确的现状”，但也不应因为代码找不到某条边就被删除。Northstar 将应用架构视图保存为 `asserted` 声明，并与代码解析的 `resolved` 关系、运行追踪的 `observed` 关系并列比较。

```bash
python3 src/northstar.py --architecture-consistency --role developer
```

结果严格分为三类：

| 结果 | Northstar 示例 | 含义 |
|---|---|---|
| `declared_and_evidenced` | `refund-worker -> create_refund` | 架构声明有代码或运行证据支持 |
| `declared_not_evidenced` | `refund-worker -> legacy_refund` | 待核验，不等于已死路径 |
| `evidenced_not_declared` | `refund-worker -> risk_check` | 影子依赖候选，需架构负责人确认 |

`knowledge_views.compare_architecture_claims()` 特意保留声明来源和实现/运行证据，而不把三类结果压缩为一个置信分数。前者回答“架构说应该怎样”，后者回答“本次索引或观察发现了什么”；它们是不同命题。这正是企业架构资产成为上下文来源而非被上下文平台取代的方式。

## 16.6 C3：任务记忆只保存工作，不自动改写组织知识

Northstar 的 `TaskMemory` 以任务 ID 保存事件序列。诊断开始、动作预览、确认、执行和验证都会追加事件，因此模型或进程重启后可以恢复任务状态，而不必重新依赖旧聊天窗口。实时队列观察则保留时间和 TTL，过期后只能当作历史证据，不能继续代表当前状态。

任务记忆和 Wiki 的职责不同：

| 载体 | 保存什么 | 如何进入长期知识 |
|---|---|---|
| 任务记忆 | 已做检查、被排除假设、待确认动作、回执 | 事故关闭后形成候选 |
| Wiki | 稳定解释、导航与已审核摘要 | 由明确来源和审核记录生成 |
| Runbook/政策/代码 | 规范或原始事实 | 由其所有者修订并重新摄取 |

因此，一次事故中“`retry_backoff` 曾被设为 60 秒”不能自动成为下一次事故的根因结论。它应保留版本和适用条件，先作为诊断线索；经过复盘与所有者审核后，才可能更新 Runbook 或监控规则。

## 16.7 C3 的验收与生产边界

```bash
python3 -m unittest tests.test_domain_model tests.test_architecture_consistency tests.test_northstar -v
```

这些测试分别保护：实体与边契约、架构声明与证据的三类差异、图遍历 ACL、Wiki 血缘与角色安全域、任务记忆隔离。它们不是图谱“准确率”的统计估计；真实企业仍需要对代码解析精度、未解析边、页面忠实度、增量延迟和人工审核成本做评测。

下一章进入 C4 和 C5。它不会给 Agent 一堆未经分类的检索片段，而是将证据、派生 Wiki、运行观察、任务记忆、缺口和工具可见性组织成 Context Package，并将读权限与写权限保持分离。

## 延伸阅读

- Tree-sitter, [Documentation](https://tree-sitter.github.io/tree-sitter/)。
- SCIP contributors, [SCIP](https://github.com/scip-code/scip)。
- W3C, [PROV-O](https://www.w3.org/TR/prov-o/)。
- Thoughtworks, [现代企业架构框架（MEAF）V4 学习镜像](https://web3d.github.io/meaf-book/)；镜像标注版权归 Thoughtworks。
