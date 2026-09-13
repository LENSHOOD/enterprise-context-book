# 附录

## A. 核心术语

**企业上下文（Enterprise Context）**：智能体要在当前身份、时间和任务下正确理解情况并开展工作，所需要的信息和约束；首次系统定义见第 1 章。<br>
**企业架构（Enterprise Architecture，EA）**：用结构化方式说明企业的业务、组织、应用、数据和技术怎样共同支持目标，并持续管理这些关系；本书把企业架构资产作为企业上下文来源，不展开完整 EA 方法论；见第 2、8 章。<br>
**元模型（Metamodel）**：规定一种模型允许出现哪些概念和关系，相当于“模型的规则”；企业架构和知识建模都可以用它约束描述语言；见第 8 章。<br>
**视角/视图（Viewpoint/View）**：视角规定如何组织某类关注点，视图是据此形成的架构表达；见第 6 章。<br>
**领域驱动设计（Domain-Driven Design，DDD）**：围绕领域模型和共享语言组织复杂软件设计的实践；本书主要借用其限界上下文、统一语言和领域事件；见第 8 章。<br>
**限界上下文（Bounded Context）**：某套模型和词义保持一致的明确边界；不同边界可保留同名但不同义的概念；见第 8 章。<br>
**Northstar Commerce**：本书虚构的在线零售企业与贯穿案例；首次出现于第 1 章，第 14—17 章给出可运行的教学参考实现。<br>
**知识库（Knowledge Base）**：保存可复用事实、规则、解释和关系的基础设施；见第 3 章。  
**原始来源（Raw Source）**：尚未被知识系统改写，能够作为事实依据的材料；见第 3 章。<br>
**派生知识（Derived Knowledge）**：系统根据来源加工出的块、向量、关系、摘要与 Wiki；来源变化时，它们可以失效并重新生成；见第 3 章。<br>
**记忆（Memory）**：围绕会话、用户、任务、Agent 或组织经历形成的受治理状态；见第 3、9 章。  
**实时状态（Runtime State）**：必须在使用时从业务系统读取并带观察时间与 TTL 的动态事实；见第 3 章。  
**任务上下文（Task Context）**：当前目标、范围、约束、进度与临时假设；见第 3 章。  
**Provenance**：记录一项知识来自哪里、经过什么转换、最后怎样被使用；见第 7、11 章。<br>
**Lineage**：记录加工结果依赖哪些输入，来源变化后可据此判断什么需要失效和重建；见第 11 章。<br>
**逻辑对象（Logical Object）**：跨版本保持身份的企业对象；见第 11 章。  
**版本对象（Version Object）**：逻辑对象在特定内容和时间下的不可变版本；见第 11 章。  
**双时间（Bitemporal Time）**：同时记录业务有效时间与系统观察时间；见第 11 章。  
**Snapshot**：一次可复现查询所固定的知识版本边界；见第 10、11 章。  
**Snapshot Manifest**：声明哪些词法、向量、图和 Wiki 投影可以共同服务的清单；见第 10 章。  
**Context API**：按身份、任务和预算返回上下文的服务契约；见第 10、17 章。  
**Context Package**：系统在权限和 Token 预算内，专门为一次任务整理的结构化材料；见第 17 章。<br>
**召回前鉴权（Pre-retrieval Authorization）**：内容进入候选列表和相关性打分之前，先按当前用户执行权限过滤；见第 12 章。<br>
**降级通道（Degraded Channel）**：本应参与查询但因故障或策略关闭的检索通道；见第 10、17 章。  
**权威来源（Authoritative Source）**：对某类声明拥有组织裁决权的来源；见第 4、11 章。  
**词法检索（Lexical Retrieval）**：依赖词项匹配的 BM25 等检索方式；见第 5 章。  
**向量检索（Dense Retrieval）**：根据嵌入空间相似度召回语义相关对象；见第 4、5 章。  
**离线语义代理通道（Offline Semantic Proxy）**：Northstar 用同义词表与 Jaccard 模拟的零依赖通道，不等同于向量检索；见第 15 章。  
**混合检索（Hybrid Retrieval）**：融合词法、向量、图和结构过滤的候选生成方式；见第 5 章。  
**RRF**：用排名倒数而非原始分数合并多个结果列表的方法；见第 5 章。  
**编译式 Wiki（Compiled Wiki）**：由来源和结构按 Schema 生成、带血缘并可增量失效的解释层；见第 7 章。  
**能力问题（Competency Question）**：领域模型建好后必须真正答得出来的验收问题；它也用来确定最小建模范围；见第 8 章。<br>
**本体（Ontology）**：共享领域中概念、关系和约束的形式化定义；见第 8 章。  
**规范实体（Canonical Entity）**：多个来源别名解析后共同指向的稳定对象；见第 8 章。  
**证据等级（Evidence Tier）**：关系来源的五级枚举：`deterministic`、`resolved`、`asserted`、`heuristic`、`inferred`；运行观察作为独立的 `observed` 等级保留，见第 8 章。  
**ArtifactFS**：本书对“固定版本源码存放处”的通用称呼；它按仓库和提交提供不可变源码 blob、路径、行号与内容散列；见第 5、18 章。<br>
**LSP（Language Server Protocol）**：编辑器与语言分析器之间的标准协议，可提供定义跳转、引用查找、类型信息和诊断；见第 5、18 章。<br>
**ADR（Architecture Decision Record）**：记录架构决策背景、选择与后果的版本化文档；首次展开见第 1 章。<br>
**Runbook**：供运维或业务处置使用的运行手册，包含症状、检查、动作和验证；首次展开见第 1 章。<br>
**知识候选（Knowledge Candidate）**：尚未通过审核、不能直接晋升为组织知识的经验或声明；见第 9 章。  
**任务记忆主体（Task-memory Subject）**：限定记忆归属、读写权限和生命周期的任务标识；见第 9、17 章。  
**Tombstone**：不保留原文的删除标记，用来防止迟到事件恢复已撤销对象，并推动各类索引和派生内容一起删除；见第 11 章。

进一步的论文、项目与官方资料参见[研究索引](/research-notes)。

## B. 阅读地图

- RAG：[Lewis et al., 2020](https://arxiv.org/abs/2005.11401)
- 层级检索：[RAPTOR](https://arxiv.org/abs/2401.18059)
- 图谱检索：[GraphRAG](https://arxiv.org/abs/2404.16130)
- Agent 记忆：[Mem0](https://arxiv.org/abs/2504.19413)
- RAG 评测：[RAGAS](https://arxiv.org/abs/2309.15217)
- 代码 Wiki：[CodeWiki](https://aclanthology.org/2026.findings-acl.288/)
- 代码语义索引：[SCIP](https://github.com/scip-code/scip)
- Agent 集成：[MCP](https://modelcontextprotocol.io/specification/)
- 企业架构历史：[Zachman, 1987](https://doi.org/10.1147/sj.263.0276)
- 架构描述标准：[ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html)
- 企业架构方法：[TOGAF](https://www.opengroup.org/togaf)
- 现代企业架构实践：[MEAF V4 学习镜像](https://web3d.github.io/meaf-book/)（镜像标注版权归 Thoughtworks）
- 领域建模：[Eric Evans, Domain-Driven Design](https://www.pearson.com/en-gb/subject-catalog/p/domain-driven-design-tackling-complexity-in-the-heart-of-software/P200000009375/9780321125217)

## C. 技术替换矩阵

| 能力 | 基线 | 规模化替代条件 |
|---|---|---|
| 元数据 | PostgreSQL | 按租户/时间分区 |
| 词法检索 | PostgreSQL FTS | 复杂代码搜索或高 QPS 时使用搜索引擎 |
| 向量 | pgvector | 向量规模和延迟证明需要专用服务 |
| 图 | 关系表/NetworkX | 多跳规模和延迟证明需要图数据库 |
| 源码 | Git partial clone | 大仓 Blob 供给成为瓶颈时按需文件系统 |
| 语义 | Tree-sitter | 重点语言增加 SCIP/编译器索引 |

## D. 评测资产与发布检查

### D.1 Golden Question Schema

每条题目至少包含 `id`、`bucket`、`question`、`role`、`mode`、必要证据 `expected_ids` 或禁止证据 `forbidden_ids`。生产题集还应记录 `difficulty`、`expected_refusal`、`expected_conflict`、`annotator`、`annotated_at` 和 `snapshot`。Northstar 的 24 条教学样本位于 `examples/enterprise-case/data/golden-questions.json`。

### D.2 答案评分 Rubric

| 维度 | 3：满足 | 2：基本满足 | 1：明显不足 | 0：失败 |
|---|---|---|---|---|
| 证据充分性 | 必要证据齐全且无禁止证据 | 缺少次要证据 | 缺关键证据 | 无证据或越权证据 |
| 引用精确性 | 引用可解析到固定版本与坐标 | 版本固定但坐标较粗 | 仅指向来源首页 | 引用无效或不存在 |
| 结论正确性 | 与标注事实一致 | 主结论正确、细节有误 | 仅部分正确 | 错误或相反 |
| 边界声明 | 冲突、缺口与不确定性均明确 | 遗漏一类边界 | 把候选当作确定事实 | 隐瞒缺口或越权行动 |

### D.3 消融记录模板

| 通道组合 | 题型 | Recall@K | MRR | nDCG@10 | 引用精确率 | P95 延迟 | 结论 |
|---|---|---:|---:|---:|---:|---:|---|
| BM25 + 图 | 关系影响 | 待测 | 待测 | 待测 | 待测 | 待测 | 教学模板，不是实测结果 |

### D.4 发布检查表

勾选状态是当前候选的可复核状态；发布裁决以 `reviews/run_manifest.json` 为唯一事实源。

- [ ] 字数达到宪章目标——运行 `python3 scripts/wordcount.py`；
- [ ] 外部事实和集中参考文献完成声明级核验——人工审计并记录日期；
- [x] Mermaid 与代码块可渲染——运行 `npm run docs:build`，并确认构建产物没有带 Mermaid 语言类的 `<pre>` 元素；
- [x] Northstar 与 Linux fixture 测试通过——运行两个案例目录的 `unittest discover`；
- [x] ACL、跨租户、提示注入和写动作边界测试存在——见 `test_northstar.py` 与 `test_action_boundary.py`；
- [x] 领域模型约束实例数据——见 `test_domain_model.py`；
- [x] 24 条教学 Golden Questions 可执行——见 `test_golden_questions.py`；
- [ ] 浏览器桌面与移动 QA 重新完成——需要发布候选构建后的人工记录；
- [x] AI 使用与事实核验方法公开——见附录 E、F；
- [x] 正文和代码使用完整许可文本——见根目录 `LICENSE` 与 `LICENSE-CODE`。

## E. AI 辅助写作声明

作者为唯一署名者和最终责任人。AI 用于资料检索、整理、草稿、引用检查和代码辅助。外部事实以论文、标准或官方文档核验；综合判断与来源陈述分开；没有可验证来源的事实不进入定稿。

## F. 研究与引用方法

本书优先使用四类来源：用奠基论文了解一个方法最初要解决什么问题、做过什么实验；用官方规范确认协议和数据模型；用项目文档与源码核对实现能力；用综述梳理技术发展。项目自行公布的基准，只用来说明它公开报告了什么，不会被写成对其他场景也成立的保证。本书自己的架构判断，则用“应、可以、建议”等措辞与来源事实区分开。

检索过程从已有调研材料建立主题地图，再围绕每章补充原始来源。关键链接在发布候选阶段实际请求验证，VitePress 同时执行内部死链检查。动态项目可能在出版后改名、迁移或更新结论，因此链接只证明发布时可访问，读者在作出工程决策前仍应检查当前版本、许可证、变更记录和适用环境。

代码知识库章节尤其区分“语法候选、名称解析、编译级关系和运行观察”。Linux 集成报告如实保留未解析数量和宏误识别，不把高覆盖召回包装成精确调用图。企业案例的数据均为虚构 fixture；它证明接口与治理契约，不代表对真实企业规模的性能承诺。

## G. 版本与勘误

正文引用以仓库提交为出版版本。事实错误、失效链接、代码回归和术语歧义可通过仓库 Issue 提交，修订记录进入 `CHANGELOG.md`。涉及外部事实的勘误应附可复核来源；涉及案例行为的勘误应附最小复现与测试。v1.0 之后新增技术不会无声改写旧结论，而会通过版本记录说明新增证据、适用范围和兼容性变化。
