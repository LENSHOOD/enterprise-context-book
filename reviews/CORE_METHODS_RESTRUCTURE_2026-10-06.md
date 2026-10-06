# 核心方法、技术选择与平台工程复核

日期：2026-10-06。候选：v1.0.0-rc.14。基线：5313fed（rc.13）。

## 结论与范围

本轮将第一部分的逻辑架构作为章节分工依据，重整第二部分的方法与技术选择，以及第三部分的工程实现。第一章只给资源、平台和任务上下文的整体关系；第三章分别展开三个部分。第二部分解释怎样准备、查找、组织、建模和使用资源；第三部分落实服务、版本、权限、执行、恢复和质量保障。第四部分保留解释案例设计的叙事，其原理依据可在前文找到。

对技术的核查以官方规范、官方仓库及固定提交的说明为主，结合社区检索发现候选。共整理 48 条来源记录，覆盖 38 个不同项目仓库，另有标准、工程文章与课程资料。完整来源与采集时间见 [技术证据台账](CORE_TECH_EVIDENCE_2026-10-06.jsonl)。仓库关注度、维护声明和最近推送分开记录，没有据此推断生产部署量、精度或吞吐排名。

其中一项为非公开参考资料，按作者要求仅保留来源标记，不提供访问地址。

## 章节职责与迁移

| 章节 | 方法或工程责任 | 本轮处理 |
|---|---|---|
| 1、3 | 三个核心部分的整体与展开 | 1.4 只保留整体；3.3 补全任务条件、依据、进展与边界；方法导航不再依赖案例章节 |
| 4 | 来源与可引用证据 | 来源盘点、结构恢复、证据单元、使用条件，再比较解析与流水线技术 |
| 5 | 检索与查询方法 | 区分表示、索引、通道、融合与重排，补结构化指标查询和后端选择 |
| 6 | 关系与层级导航 | 接收原第8章的图检索、社区摘要和代码结构内容，统一有界取证与验证 |
| 7 | 编译式知识视图 | 来源、模板、声明、检查、发布与更新，核查代码 Wiki 项目的实际维护能力 |
| 8 | 业务建模与本体 | 从问题和证据走到对象、关系、状态、规则、动作、映射与实例验证，取消品牌实践拼接 |
| 9 | 任务上下文与记忆 | 补齐材料构造、预算、刷新、恢复和记忆生命周期，再列技术职责 |
| 10 | 平台接口与可靠交付 | 完整请求/响应、有效任务条件、缺口决策、异步恢复、缓存与故障 |
| 11 | 身份、时间与变更 | 明确记录时间与采样时间，版本身份与内容散列分离，补校验与更新实现 |
| 12 | 安全与受控行动 | 通用状态机、批准、并发、幂等、回执、验证、部分成功及事件级联 |
| 13 | 评测与运行保障 | 区分教学与生产发布门，增加影子副作用隔离和工具选择 |
| 14—18 | 应用与练习 | 更新失效引用，案例仍解释具体设计及实现范围，不承担首次补全通用机制 |

## 技术覆盖判断

“通用方法”“专门实现”“研究增强”是不同维度。专用代码索引协议即使关注度不高，也不因此成为不成熟方法；高关注度工具也可能含实验配置或商业托管能力。正文按任务需要和可验证契约选择技术，不以项目列表替代方法。

| 方法族 | 核查的代表性实现 | 书中采用的判断 |
|---|---|---|
| 文档结构恢复 | Docling、Unstructured | 保留版面、表格与坐标的方法；具体文件质量仍需抽样 |
| 词法和向量检索 | Elasticsearch、OpenSearch、pgvector、Qdrant、Milvus、Weaviate、Faiss | 产品能力交叉；表示、索引、过滤、融合、重排分别比较 |
| 表示与重排模型 | Sentence Transformers、FlagEmbedding | 模型工具链与数据库分开；没有给出未经实测的领域效果排名 |
| 结构导航 | Tree-sitter、SCIP、LSP、PageIndex | 语法、语义索引、交互协议和文档树分别定位 |
| 生成主题结构 | RAPTOR、Microsoft GraphRAG、LightRAG | 用于特定综合问题，先与普通检索和关系查询对照 |
| Wiki 维护 | CodeWiki、OpenWiki | 已有增量或声明维护能力；不将其宣称为完整企业治理平台 |
| 业务模型与校验 | JSON Schema、Pydantic、Neo4j、Jena、pySHACL | 数据结构、实例约束、关系查询和形式推理分别说明 |
| 指标与资产结构 | MetricFlow、Backstage | 作为指标语义及软件资产实践参照，不代替通用企业本体 |
| 上下文与记忆 | LangChain、LlamaIndex、Haystack、LangGraph、Mem0、Graphiti、Cognee | 组件编排、持久状态、个体记忆和时间关系分别定位 |
| 策略与恢复 | OPA、OpenFGA、Temporal | 决策与执行分开；框架不能替代业务授权和外部幂等 |
| 质量与观测 | Ragas、DeepEval、OpenTelemetry | 模型裁判需校准，追踪不等于业务验证或可靠账本 |

核查还修正了几处容易误导的具体表述：pgvector 的已有系统前提是 PostgreSQL；Faiss 自带索引保存与加载，应用仍负责事务、版本发布和恢复管理；Microsoft GraphRAG 明确处于维护模式；CodeWiki 和 OpenWiki 已有更新机制；开源、托管功能和不同年份论文结果分别归属。对应证据均保留在台账。

## 建模方法的吸收与边界

阅读了所提供课程“建本体”的全部正文单元，并核对当前建模原则页。可借鉴的是从实际任务与业务流程取得依据，再识别对象、状态、关系、触发规则、动作读写、数据映射和实例调试。书稿将这些做法纳入自己的退款设计示例，非公开出处仅在内部研究记录中保留；未复制受限课程原文或发布访问口令。

没有把课程中的所有关系必须顺着流程方向、动作必须归入固定产品类别等约定提升为通用标准。关系方向服从业务谓词，流程先后通过步骤依赖和事件表达；形式本体、业务规则、工作流和实际授权分别承担责任。演示中的调试发现也不被当成生产成功证明。

## 独立复核与处置

已修正：任务缓存缺任务ID和记忆主体；接口响应缺服务端确认后的目标、完成标准与口径；系统记录时间与实际采样时间混用；版本ID与正文散列混用；影子运行缺少副作用隔离；教学金标与生产统计门槛混写；Linux章节仍引用已撤换的建模步骤。

结构和工程复核已再次确认上述问题闭合，未发现新的阻断项。技术复核中的 PostgreSQL 前提与 Faiss 索引读写表述也已修正，并核对固定提交的读写接口。

保留第四部分的设计解释，是为了让读者理解案例代码为何这样实现。没有采纳将案例改成纯命令操作手册的建议；已收敛重复泛论并补齐向第4—13章的原理引用。

## 验证与限制

候选构建和 133 项 Northstar、21 项 Linux 测试通过。第13章消融实际运行结果与正文一致：BM25、代理、融合的 Recall@5 分别为 0.8056、0.8056、0.8333，约束通过数分别为 11/12、10/12、11/12。核心章节的 5 个 JSON 示例已执行语法解析检查；第10章请求和响应的目标、完成条件及条目引用另行核对通过。图形、最终发布版本和部署结果另按最终候选核验。

浏览器已检查第1、3、4—13章，确认标题、图形与正文可加载；第8章390 px视口无页面横向溢出。将过宽的流程图改为纵向阅读，行动状态图采用成功主路径与异常转移表配合，保留完整控制条件。构建只有已有的大包体积提示；验证不把教学代码测试通过解释为通用生产契约已经实现。

本轮没有部署所有外部工具，没有做采购市场调查，也没有独立复现项目宣传中的基准。技术选择表提供有来源的代表性选项和验证条件，不保证其中某个方案普遍最好。新增接口与状态机是通用设计契约，不是声称当前教学代码已经实现网络服务、持久编排或生产缓存。

## 来源索引

下面列出本次核查的来源身份，能力与维护判断详见机器可读台账。取回日期统一为 2026-10-06；仓库数据是当次观察快照。
- RET-ELASTIC：[elastic/elasticsearch — README.asciidoc](https://github.com/elastic/elasticsearch/blob/8e72cdd116e04ca05af71fec4e642a7723eda1f5/README.asciidoc)。
- RET-OPENSEARCH：[opensearch-project/OpenSearch — README.md](https://github.com/opensearch-project/OpenSearch/blob/bd8160a6aa14516ba255a791cc803cdc0f9ad1ec/README.md)。
- RET-PGVECTOR：[pgvector/pgvector — README.md](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/README.md)。
- RET-QDRANT：[qdrant/qdrant — README.md](https://github.com/qdrant/qdrant/blob/016542aa5deb6c66380bb137badf73d54f742bde/README.md)。
- RET-MILVUS：[milvus-io/milvus — README.md](https://github.com/milvus-io/milvus/blob/243ebd872bbd5a846d03b7fede2b4e1c0856e739/README.md)。
- RET-WEAVIATE：[weaviate/weaviate — README.md](https://github.com/weaviate/weaviate/blob/70d0d68aadd3eaaf1d6ef7997a45b73786a3995a/README.md)。
- RET-FAISS：[facebookresearch/faiss — README.md](https://github.com/facebookresearch/faiss/blob/83ae8b0908312c1e40734a806a3cc435b64f9496/README.md)。
- RET-DOCLING：[docling-project/docling — README.md](https://github.com/docling-project/docling/blob/d15cf10c26cf33c54ef2779a1fd9d4e3066d07e0/README.md)。
- RET-UNSTRUCTURED：[Unstructured-IO/unstructured — README.md](https://github.com/Unstructured-IO/unstructured/blob/67f4cf1b7268068f1a58c09d1fb2f7045df6fc85/README.md)。
- RET-SENTENCE-TRANSFORMERS：[huggingface/sentence-transformers — README.md](https://github.com/huggingface/sentence-transformers/blob/4a3b5cd6ec718e421f57e824a41ed3fd99595df6/README.md)。
- RET-FLAGEMBEDDING：[FlagOpen/FlagEmbedding — README.md](https://github.com/FlagOpen/FlagEmbedding/blob/fd1a2bdf69488ffebe0327999d4400d8c8058a0b/README.md)。
- RET-TREE-SITTER：[tree-sitter/tree-sitter — README.md](https://github.com/tree-sitter/tree-sitter/blob/752c612a1359f00e4c113593837a0c1e880214e3/README.md)。
- RET-SCIP：[scip-code/scip — README.md](https://github.com/scip-code/scip/blob/f07c097d9b5d952c50eecde328200e454937fa09/README.md)。
- GM01：[microsoft/graphrag — README: maintenance notice and repository guidance](https://github.com/microsoft/graphrag/blob/00adeaf713d9bca070d28476bdd21234dce6ecc4/README.md#L4)。
- GM02：[HKUDS/LightRAG — README: graph/vector retrieval and update boundaries](https://github.com/HKUDS/LightRAG/blob/b9ec0644f9c48000ba93116265b2f1adf496a645/README.md#L261)。
- GM03：[VectifyAI/PageIndex — README: reasoning over document trees and cloud scope](https://github.com/VectifyAI/PageIndex/blob/91238b33b625b51a797db591f9719d97716e5c4e/README.md#L46)。
- GM04：[FSoft-AI4Code/CodeWiki — README: dependency-driven documentation and incremental updates](https://github.com/FSoft-AI4Code/CodeWiki/blob/0815b547a28640f15b73e714b6259189bfc57f06/README.md#L41)。
- GM05：[langchain-ai/openwiki — README: grounded claims, source drift and durable wiki updates](https://github.com/langchain-ai/openwiki/blob/0f2060fe884a3a7bb7cc880c8c4f066267771483/README.md#L19)。
- GM06：[mem0ai/mem0 — README: personalized memory, algorithm evolution and managed benchmark boundary](https://github.com/mem0ai/mem0/blob/5dbf071356e4b9fc81ed924d51586926c4c48a63/README.md#L45)。
- GM07：[getzep/graphiti — README: temporal context graphs and Graphiti/Zep boundary](https://github.com/getzep/graphiti/blob/683a8539c8925de69071a1305dc8bf0e52e17c65/README.md#L37)。
- GM08：[topoteretes/cognee — README: connected memory, session distillation and operations](https://github.com/topoteretes/cognee/blob/81b08fb350dae167964beae67cef5d0389dc3559/README.md#L42)。
- GM09：[langchain-ai/langgraph — README: stateful orchestration, persistence and memory](https://github.com/langchain-ai/langgraph/blob/37014c09b9fafbfec9f336da80d8624d75a9ff7f/README.md#L12)。
- GM10：[deepset-ai/haystack — README: modular retrieval and agent pipelines](https://github.com/deepset-ai/haystack/blob/97677b88f5f6f72a4251c177cd2c03280dc91e48/README.md#L12)。
- GM11：[run-llama/llama_index — README: general data framework and company focus shift](https://github.com/run-llama/llama_index/blob/7d69c2f1d7207aaf51f65696572dcfaf8719678a/README.md#L11)。
- GM12：[langchain-ai/langchain — interoperable application framework and orchestration boundary](https://github.com/langchain-ai/langchain/blob/2dd956b8add667dac4f97605ae441d75b8ae228e/README.md#L24)。
- GM13：[Microsoft GraphRAG official documentation — indexing and query modes](https://github.com/microsoft/graphrag/blob/00adeaf713d9bca070d28476bdd21234dce6ecc4/docs/index.md#L36)。
- ENG01：[neo4j/neo4j — README and official repository documentation](https://github.com/neo4j/neo4j/blob/2026.09/README.asciidoc)。
- ENG02：[apache/jena — README and official repository documentation](https://github.com/apache/jena/blob/main/README.md)。
- ENG03：[RDFLib/pySHACL — README and official repository documentation](https://github.com/RDFLib/pySHACL/blob/master/README.md)。
- ENG04：[pydantic/pydantic — README and official repository documentation](https://github.com/pydantic/pydantic/blob/main/README.md)。
- ENG05：[python-jsonschema/jsonschema — README and official repository documentation](https://github.com/python-jsonschema/jsonschema/blob/main/README.rst)。
- ENG06：[temporalio/temporal — README and official repository documentation](https://github.com/temporalio/temporal/blob/main/README.md)。
- ENG07：[open-policy-agent/opa — README and official repository documentation](https://github.com/open-policy-agent/opa/blob/main/README.md)。
- ENG08：[openfga/openfga — README and official repository documentation](https://github.com/openfga/openfga/blob/main/README.md)。
- ENG09：[open-telemetry/opentelemetry-specification — README and official repository documentation](https://github.com/open-telemetry/opentelemetry-specification/blob/main/README.md)。
- ENG10：[backstage/backstage — README and official repository documentation](https://github.com/backstage/backstage/blob/master/README.md)。
- ENG11：[dbt-labs/metricflow — README and official repository documentation](https://github.com/dbt-labs/metricflow/blob/main/README.md)。
- ENG12：[vibrantlabsai/ragas — README and official repository documentation](https://github.com/vibrantlabsai/ragas/blob/main/README.md)。
- ENG13：[confident-ai/deepeval — README and official repository documentation](https://github.com/confident-ai/deepeval/blob/main/README.md)。
- MAIN-OWL：[OWL 2 Web Ontology Language Document Overview (Second Edition)](https://www.w3.org/TR/owl2-overview/)。
- MAIN-SHACL：[Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/)。
- MAIN-RDF：[RDF 1.1 Concepts and Abstract Syntax](https://www.w3.org/TR/rdf11-concepts/)。
- MAIN-JSONSCHEMA：[What is JSON Schema?](https://json-schema.org/overview/what-is-jsonschema)。
- MAIN-PROV：[PROV-O: The PROV Ontology](https://www.w3.org/TR/prov-o/)。
- MAIN-RRF：[Reciprocal rank fusion | Elasticsearch Reference](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)。
- MAIN-CONTEXT：[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。
- MAIN-PERSISTENCE：[Persistence - Docs by LangChain](https://docs.langchain.com/oss/python/langgraph/persistence)。
- MAIN-COURSE：非公开建模参考资料，不提供访问地址。
