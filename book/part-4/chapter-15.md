# 第 15 章 建立可信证据检索

> 本章要回答：如何从无商业 API 的最小基线出发，建立权限正确、引用可核验的证据检索？

第一条纵向切片只回答一个问题：在任何生成模型参与之前，平台能否按身份找到正确、版本化且可引用的证据？如果这条链路不可靠，加入嵌入、重排和 Agent 只会让错误更流畅。

配套原型使用 Python 标准库和 JSON，读者无需数据库或模型密钥即可运行。它不是最终性能方案，而是一份可执行规格：对象包含 ACL 和版本，权限在评分前执行，每个结果都返回稳定引用，测试能证明不同角色看见不同集合。

## 15.1 运行最小切片

进入案例目录并运行查询：

```bash
cd examples/enterprise-case
python3 src/context_demo.py \
  "handle_order_cancelled create_refund order.cancelled" \
  --role developer
```

然后执行测试：

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖三条基础契约：开发者能找到代码与架构决策；客服不能看到代码和工程 Runbook；每个命中都有版本化引用。这里故意使用包含符号的查询，因为它能验证 BM25 对精确标识符的优势。

数据对象示意如下：

```json
{
  "id": "refund-handler",
  "kind": "code_symbol",
  "title": "handle_order_cancelled",
  "text": "Consumes order.cancelled and calls create_refund",
  "acl": ["developer", "incident_commander"],
  "citation": "code://northstar/payment@c1/handlers.py#handle_order_cancelled"
}
```

检索函数先根据 `acl` 过滤可见对象，再计算 BM25。即使无权代码与查询完全匹配，它也不会进入评分候选。生产实现会把简单角色替换为策略 ID 与主体属性，但顺序不变。

## 15.2 为什么先做无依赖基线

最小实现有三个用途。第一，它把预期行为固定成测试，后续迁移数据库时可以进行黑盒对照。第二，它让读者观察排序与 ACL，而不被模型和基础设施故障干扰。第三，它建立可降级路径：完整语义服务不可用时，仍有一个安全、可解释的词法检索。

基线不追求生产级中文分词、海量并发或真实向量召回。正则会把中文切成单字，这通常抬高表面召回并降低精确率；生产系统应使用经过题集验证的中文分词或子词切分。示例只适用于 fixture 规模。

一个值得保留的设计是纯函数式查询：输入查询、主体、范围和快照，输出结构化候选。数据存储、评分器和重排器可以替换，权限与引用契约由测试保护。

## 15.3 结构分块与父子对象

下一步摄取 Markdown、OpenAPI 和代码时，不应按固定字符切块。政策按标题和条款解析，ADR 保留 Context、Decision、Consequences，Runbook 保留症状、检查、动作和验证，代码按符号切分。

每个叶子块保存 `parent_id`。查询命中某条政策时，返回该条款及必要父节；命中函数时，返回签名、注释、实现和所在模块说明。父块补充上下文，但引用仍精确指向叶子和版本。

摄取测试使用小型 fixture 检查标题路径、代码行号、内容散列和 ACL 继承。解析失败的对象进入隔离队列，不能用裸文本静默替代后发布，因为那会丢失引用和安全元数据。

## 15.4 迁移到 PostgreSQL 与全文索引

案例完整模式使用 PostgreSQL 保存对象清单、版本、ACL 和血缘。正文可使用 PostgreSQL 全文搜索或独立搜索引擎，向量使用 pgvector。选择 PostgreSQL 是为了降低教学部署数量，不意味着它适合所有企业规模。

逻辑表可以包括：

```sql
CREATE TABLE knowledge_version (
  version_id text PRIMARY KEY,
  object_id text NOT NULL,
  kind text NOT NULL,
  tenant_id text NOT NULL,
  source_uri text NOT NULL,
  source_revision text NOT NULL,
  content text NOT NULL,
  content_hash text NOT NULL,
  valid_from timestamptz,
  valid_to timestamptz,
  acl_policy_id text NOT NULL,
  metadata jsonb NOT NULL
);
```

实际 Schema 还需版本表、来源表、策略映射和派生血缘。全文与向量索引存 `version_id`，不各自复制真相。查询事务先解析主体和 Manifest，再把租户、ACL、有效时间与快照编译成过滤条件。

pgvector 为 PostgreSQL 提供向量相似搜索以及 HNSW、IVFFlat 等索引能力。[pgvector](https://github.com/pgvector/pgvector) 索引选择要基于数据量、召回、构建时间和更新模式评测；案例可以先精确搜索，再在数据扩大后启用近似索引。

## 15.5 构建离线语义代理通道

配套教学原型没有调用嵌入模型，而是用确定性同义词表扩展查询词和文档词，再用两组词项的 Jaccard 相似度（交集大小除以并集大小）排序。选择它是为了让案例零依赖、可离线运行且分数可解释；它只能验证语义通道、融合与降级契约，检索质量不能外推到生产。生产系统应将该代理替换为经过企业题集评测的嵌入模型。

嵌入输入不应只有正文。对短代码符号，可以组合规范名称、路径、签名和摘要；对政策条款，组合标题路径与正文；对 Wiki，组合对象类型、标题和解释。不同类型可以采用同一嵌入模型，但需分别评测。

模型与预处理版本进入索引元数据。升级嵌入模型时构建新索引，不在同一空间混用向量。无商业 API 模式可以使用本地 Sentence Transformers，或关闭向量通道继续运行 BM25；案例命令必须明确当前启用了哪些通道。

语义查询同样先应用安全和范围过滤。如果后端只能检索后过滤，会在小权限集合中丢失召回，甚至暴露候选元数据。生产方案应验证过滤语义，必要时按租户或安全域分区。

## 15.6 RRF 与任务感知重排

BM25 与向量分别返回带名次的候选，使用 RRF 融合：

```python
score[document_id] += 1.0 / (60 + rank)
```

常数 60 是常见基线，不是普遍最优。融合后先按对象 ID 去重，再根据任务类型、来源权威、新鲜度和对象类型调整。重排特征必须可记录，避免模型分数成为无法解释的黑箱。

代码定位任务提高 `code_symbol` 与 `api_schema` 配额；政策解释优先规范政策；事故诊断同时保留 Runbook、代码、部署和实时观察。来源权威性不是全局固定值，而是相对于声明类型：HR 对组织关系权威，Git 对源码权威，监控对当前指标权威。

可选交叉编码器只处理融合后的少量候选。它失败或超时时退回 RRF，响应标记 `reranker_degraded`。评测比较加入重排前后的题型收益和 P95 延迟。

## 15.7 上下文选择与引用

排序列表不能直接等于模型上下文。选择器需要去重、限制每类证据数量、补父块、保留冲突并满足 Token 预算。同源 Wiki 与原文只计作一条证据链，优先保留权威原文和帮助理解的摘要。

返回结构应包含：

```json
{
  "object_id": "refund-handler",
  "version_id": "c1:refund-handler",
  "kind": "code_symbol",
  "score": 0.0325,
  "channels": ["bm25", "graph_seed"],
  "citation": "code://northstar/payment@c1/handlers.py#handle_order_cancelled",
  "reason": "exact symbol and event match"
}
```

引用解析器验证 URI 指向当前 ArtifactFS 或来源快照中的真实对象。源码引用最好包含行区间，但符号 ID 更适合跨格式显示；二者可以同时保存。任何无法解析的引用都应在发布前被 Lint 拒绝。

## 15.8 有意保留并修复一个失败

原型使用泛化自然语言“订单取消后如何退款”时，政策可能排在代码之前。这对客服未必错误，却不能满足开发者寻找实现的意图。盲目把 Top-K 从 5 增到 50 会增加噪声，并不能稳定把代码送进最终上下文。

修复分三步。首先从查询中的符号、路径和角色识别意图；其次为标题、符号、路径和正文设置不同词法权重；最后为代码任务保留代码通道配额。若自然语言没有明确标识符，向量召回模块 Wiki，再沿图下钻到入口符号。

这个失败应进入 Golden Dataset，分别以客服和开发者身份定义预期。系统不是寻找一个“全局正确排序”，而是在任务和权限条件下选择足够证据。

## 15.9 增量更新与快照发布

摄取任务根据来源修订和内容散列计算变更。新增对象写入各索引，修改对象创建新版本，删除对象建立 tombstone 并撤销投影。只有受影响向量和全文文档重建。

候选索引完成后运行对象数量、ACL、引用和检索回归。通过后生成 Snapshot Manifest，并原子切换在线别名。向量通道未完成时可以发布一个明确的 `lexical-only` 快照，但不能把新全文与旧向量静默组合。

读者应执行两类复现：在干净目录从来源重建并运行全部测试；修改一条政策或代码 fixture，只观察相关对象版本和结果变化。两者共同证明系统不是一次性演示。

## 本章小结

可信证据检索从无依赖基线开始，以测试固定 ACL、版本和引用契约；随后增加结构分块、PostgreSQL、全文、pgvector、RRF 与任务感知重排。每条通道共享安全和快照过滤，上下文选择器负责去重、父块与证据配额。最重要的工程习惯是保留失败样本并用消融修复，而不是通过扩大 Top-K 或增加模型掩盖问题。

## 延伸阅读

- PostgreSQL, [Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)。
- pgvector, [Open-source vector similarity search for Postgres](https://github.com/pgvector/pgvector)。
- Gordon Cormack et al., [Reciprocal Rank Fusion](https://dl.acm.org/doi/10.1145/1571941.1572114), 2009。
