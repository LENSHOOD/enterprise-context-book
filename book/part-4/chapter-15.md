# 第 15 章 C0-C2：从原始来源建立可信检索

> 本章要回答：怎样从人能读懂的来源开始，逐步构建权限正确、版本可回跳、可扩展的检索？

本章完成前三个检查点。C0 先检查来源而不写任何索引；C1 把五份来源编译为对象并建立最小 BM25；C2 在同一对象契约上加入离线语义代理、RRF 与双时间选择。每一次增加复杂度之前，前一阶段的行为都已经由测试固定。

## 15.1 C0：先检查输入世界

**本检查点的产物**：五份人工可读来源和一份机器可读清单。它们不是检索结果，也不是模型摘要。

```bash
cd examples/enterprise-case
find data/raw -type f | sort
```

读者会看到：订单取消政策、退款积压 Runbook、`order.cancelled v2` 事件 Schema、退款消费者代码及其测试。`data/raw/manifest.json` 为每份来源指定解析器、稳定对象 ID、租户、ACL、版本、权威性、引用和两个时间字段。这里没有“万能文档切分器”：不同来源用不同解析器，是为了保留语义和坐标。

例如代码来源声明了要提取的 Python 符号：

```json
{
  "id": "code-refund-consumer",
  "path": "code/refund-worker/consumer.py",
  "parser": "python_symbol",
  "symbol": "handle_order_cancelled",
  "acl": ["developer"],
  "citation": "code://northstar/refund-worker@abc123/consumer.py#handle_order_cancelled"
}
```

这条记录回答了三个不同问题：文件在哪里、哪一段是对象、谁能看。把三者都塞进无结构文本后再由模型猜测，是企业知识系统最常见的不可审计起点。

## 15.2 C1：编译第一个对象集

**新增代码**：`src/build_baseline.py`。它读取 C0 的清单和来源，写出 `generated/baseline-knowledge.json`。生成目录可删除；真实输入保持在 `data/raw/`。

```bash
python3 src/build_baseline.py
```

命令应输出 `object_count: 5`。这五个对象构成可逐行检查的最小纵向切片，不是完整的 19 对象教学 fixture。后续 C2-C5 使用扩展 fixture 来集中讲检索、关系和治理；本书明确不把这个代表性编译器包装成完整企业连接器。

编译器的核心不是 JSON 序列化，而是为原文加上治理信封：

```python
text = parse_source(source_path, item["parser"], item.get("symbol"))
source_uri = f"fixture://northstar/{item['path']}@{item['version']}"
content_hash = f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"

document = {
    "id": item["id"],
    "version": item["version"],
    "citation": item["citation"],
    "acl": item["acl"],
    "source": {"uri": source_uri, "revision": item["version"]},
    "time": {"valid_from": ..., "observed_at": ...},
    "lineage": {"derived_from": [source_uri], "transform": "baseline-compiler@1"}
}
```

对象 ID 用于合并投影；内容散列用于检测变更；版本化引用用于回跳；ACL 必须跟随对象，而不是在最终回答阶段临时附加；`valid_from` 与 `observed_at` 则为后面的双时间查询留出位置。

### C1 的第一个回归测试

```bash
python3 -m unittest tests.test_build_baseline -v
```

该测试做三件事：同一份输入重复编译产生字节相同的文件；代码对象确实来自 `handle_order_cancelled`；developer 可检索到它而 support 不可检索到它。最后一项尤其重要，因为它证明权限过滤发生在排序前，而不是在结果列表截断后。

## 15.3 C1：在无依赖 BM25 上证明 ACL-first

`src/context_demo.py` 是本书唯一故意保持单文件的实现。它让读者在不跨模块跳转的情况下看见 C1 的完整查询顺序：读取数据、按角色过滤、评分、返回引用。

```bash
python3 src/context_demo.py \
  "handle_order_cancelled create_refund" \
  --role developer \
  --data generated/baseline-knowledge.json

python3 src/context_demo.py \
  "handle_order_cancelled create_refund" \
  --role support \
  --data generated/baseline-knowledge.json
```

第一个命令命中 `code-refund-consumer`，其引用以 `code://` 开头；第二个命令没有该对象。关键控制流只有两步：

```python
allowed = [doc for doc in documents if role in doc["acl"]]
hits = bm25(question, allowed)
```

不能把它反过来。若先在全局集合计算 Top-K 再过滤，权限较小的主体会因无权候选占据名次而丢失应有召回，某些后端还会泄露无权对象的计数、相似度或错误信息。生产系统会把简单角色换成策略 ID、主体属性和数据库过滤条件，但“先限定候选宇宙，再计算相关性”的顺序不变。

BM25 在这里的意义也很克制：它能精确定位 `handle_order_cancelled`、`create_refund` 和事件名，不能代表中文分词质量、企业规模延迟或语义理解能力。正因为基线简单，它能成为以后替换存储、向量模型和重排器时的行为对照。

## 15.4 C2：抽出可替换的检索通道

**新增代码**：`src/retrieval.py`。C2 不改变对象、ACL 或引用格式，只将评分通道从平台编排中抽出。该模块有三项职责：分词与同义词扩展、BM25 与离线语义代理、保留通道来源的 RRF 融合。

```python
rankings = {
    "bm25": lexical,
    "semantic_proxy": semantic,
}
ranked = reciprocal_rank_fusion(rankings, limit)
```

离线语义代理把“退款”“取消”“积压”等教学同义词扩展为稳定词项，再用 Jaccard 相似度排序。它不是嵌入模型，也不应该用于衡量生产语义检索质量。它的教学价值是验证两条通道如何共享 ACL、如何通过 RRF 融合、某条通道停用时如何在响应中暴露 `degraded_channels`。

完成后的编排器 `src/northstar.py` 仍然先调用 `visible_documents(principal)`，再把这个已经授权的集合传给 `retrieval.py`。因此替换为 pgvector、Elasticsearch 或本地嵌入模型时，替换的是通道实现，而不是安全顺序或对象契约。

### C2 的失败注入

将 `semantic_proxy` 标为停用，Context Package 会继续返回 BM25 候选，并把降级写入 `degraded_channels`。这比“模型不可用时仍生成一段没有来源的回答”可靠。相应回归测试位于 `test_context_reports_disabled_channel`。

## 15.5 C2：把业务时间与观察时间分开

政策在业务上何时生效，与平台何时看到它不是同一个问题。Northstar 保留两条时间轴：

- `valid_from` / `valid_to`：这条规则在业务世界的有效区间；
- `observed_at`：教学系统第一次摄入它的时间。

```bash
python3 src/time_demo.py
```

输出应显示：2026-07-20 的业务查询选择 `product-cancellation-policy-v1`；2026-08-15 选择新政策；若系统观察时间早于摄入时刻，则返回空集合。这个空集合不是错误，而是“当时系统尚不知道该对象”的诚实结果。

本例只保存首次观察时间，不能重建历史上每次索引修改。生产审计需要保存不可变 Snapshot Manifest、连接器水位和投影版本，详见[第 11 章](/part-3/chapter-11)。但即使是最小原型，也不能用文件写入时间伪装双时间语义。

## 15.6 从 C2 到生产检索

生产路线可以使用 PostgreSQL 保存对象清单、版本、ACL 和血缘；全文索引与 pgvector 只保存 `version_id`，而不建立第二份事实。向量模型、预处理版本和索引参数进入 Snapshot Manifest；模型升级时构建新索引，不在同一向量空间混用版本。RRF 常数 60 是起点，不是无需评测的默认真理。

代码定位、政策解释和事故诊断也不应共享一个全局排序。它们对对象类型、来源权威、新鲜度和图扩展的偏好不同。第 13 章的 Golden Dataset 与消融实验应证明某个通道真的改善某类任务，才能保留复杂度。

## 本章小结

C0 让读者先看原始事实，C1 将事实编译为带 ACL、时间、引用和血缘的对象，并用无依赖 BM25 固定“召回前鉴权”的行为。C2 把排序通道抽成可替换模块，加入离线语义代理、RRF、降级声明和双时间选择，但没有改变前一阶段的对象契约。下一章在这些已验证的对象上建立关系图、Wiki、任务记忆和企业架构差异检测。

## 延伸阅读

- PostgreSQL, [Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)。
- pgvector, [Open-source vector similarity search for Postgres](https://github.com/pgvector/pgvector)。
- Gordon Cormack et al., [Reciprocal Rank Fusion](https://dl.acm.org/doi/10.1145/1571941.1572114), 2009。
