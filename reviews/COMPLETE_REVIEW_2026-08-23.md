# 《企业上下文》v1.0-rc.1 完整审查报告

审查日期：2026-08-23  
审查范围：写作宪章、目录、18 章正文、附录、研究索引、Northstar 案例、Linux eBPF 案例、完整 Linux 番外、VitePress 站点、许可证与发布材料。  
审查目标：真实性、完整性、体系性、无歧义、可复现性、安全性、可读性和公开发布一致性。

## Executive Summary / 执行结论

当前成果已经形成清楚且有价值的企业上下文理论骨架：知识、记忆、实时状态、权限、工具与任务上下文的边界明确；RAG、层级、Wiki、图和记忆被放进统一生命周期；版本、时间、血缘、安全和评测没有被当作附属功能。第 10—13 章是全书最稳定的体系核心，Linux 实验也诚实保留了正则解析误差。

但当前版本不能通过 v1.0 发布门。阻断原因不是观点方向，而是“承诺与交付证据不一致”：Northstar 规格描述完整企业案例，仓库只交付最小只读纵向切片；第 17 章描述可行动闭环，代码没有 REST/MCP、审批、状态机、写工具和执行验证；Linux 目录承诺词法、向量、图混合检索，实际工具只有 syntax-only + BM25/FTS；发布检查表又把这些未交付项标为已通过。站点的 6 个 Mermaid 图也没有渲染，而是显示为代码块。

建议将当前状态定义为“内容完整初稿 + 可运行原型（RC）”，而不是 v1.0。若坚持 v1.0，应先完成下文 P0/P1 修订门。

## Introduction / 范围与假设

本报告回答的不是“书能否构建”，而是“书中公开承诺是否被正文、代码、测试和发布证据共同支持”。审查以仓库内的写作宪章、目录和案例规格为验收合同；当正文与实现发生冲突时，不默认任何一方正确，而是把冲突本身列为发布问题。

“真实性”分为三层：来源是否存在、来源是否支持相邻声明、仓库自述结果是否可由代码或运行证据复核。50 个唯一公开链接的健康检查覆盖第一层；RAG、RAPTOR、GraphRAG、Mem0、MCP、Tree-sitter、SCIP 和 Linux 官方文档抽样覆盖第二层 [1][2][3][4][5][6][7][8][9]；构建、测试、容器、命令和 Git tag 验证覆盖第三层 [10]。

## 评分

| 维度 | 分数 | 结论 |
|---|---:|---|
| 核心论点 | 8/10 | 统一框架成立，边界清楚 |
| 体系完整性 | 7/10 | 主干完整，Late Interaction、多跳、附录 Rubric 等缺口明确 |
| 事实与引用 | 7/10 | 50 个唯一链接可访问，抽样支持良好；缺少逐声明账本，发现书目错误 |
| 术语与无歧义 | 7/10 | 核心术语稳定；“完整”“语义”“实现”等词在案例部分有口径漂移 |
| Northstar 实战 | 3/10 | 原理描述完整，公开数据与实现远低于 CASE_SPEC |
| Linux eBPF 实战 | 6/10 | 基线真实且诚实，但未实现承诺的混合与编译级层 |
| 完整 Linux 番外 | 7/10 | 真实规模实验有价值；产物不可独立核验，解析精度低且已披露 |
| 工程质量 | 6/10 | 20 项测试、容器、构建通过；关键安全与行动路径无实现/测试 |
| 阅读与站点设计 | 6/10 | 导航与移动基础可用；架构图全部未渲染 |
| 复现与 DX | 5/10 | README 快速路径可用；第 18 章公开命令实际失败 |
| 发布与许可 | 4/10 | 仍未部署，版本口径不一，LICENSE 不是所称完整法律文本 |

综合：6.2/10。判定：**DONE_WITH_CONCERNS，v1.0 NOT CLEARED**。

## Main Analysis / 主要发现

### P0：发布阻断项

### 1. Northstar 的公开交付不符合案例规格

`CASE_SPEC.md:15-22` 要求 5 个逻辑仓、6—10 ADR、8—12 Runbook/事故复盘、OpenAPI/Protobuf、部署配置和 50—100 Golden Questions。实际 `examples/enterprise-case/data/knowledge.json` 只有 8 个知识对象：1 个 Runbook、1 个 ADR、1 个 policy、1 个 schema、1 个 incident 和 3 个代码对象；没有公开 Golden Dataset、OpenAPI、Kubernetes 配置或 5 个真实逻辑仓。

影响：第 14—17 章可以作为架构说明，却不能称为“完整案例”或证明企业上下文完整生命周期。`RELEASE_AUDIT.md:9` 的“通过”应撤销，直到规格被实现；另一种选择是正式缩小 `CASE_SPEC.md` 和宪章承诺，把它明确改名为“最小纵向切片”。

### 2. “从证据到行动”的核心闭环没有实现

`CASE_SPEC.md:42-43` 和 `book/part-4/chapter-17.md:66-123` 描述 REST/MCP、`prepare_replay`、审批令牌、幂等、任务状态机、审计和执行后验证。实际 `northstar.py` 只提供进程内 search、trace、Wiki、memory、runtime read 和 JSON CLI；没有服务端接口、MCP、写工具、策略网关或状态机。

影响：全书核心差异化主张“知道与能做分权治理”只停留在文字。v1.0 至少应实现一个受控写动作的完整本地闭环，并用提示注入、越权、过期审批、重复执行和执行后验证测试证明。

### 3. 发布审计与附录存在错误通过声明

`book/appendices.md:42` 声称图表可渲染，但构建产物将 6 个 Mermaid 块输出为 `language-mermaid` 代码块；没有 Mermaid 插件或客户端渲染。`book/appendices.md:45` 声称注入边界测试存在，但 20 项测试没有提示注入、工具审批或写操作测试。`RELEASE_AUDIT.md:7` 又以“超过 8 万字符”替代宪章的“8—12 万字”。

影响：审计文件本身不可信。发布前应把所有 `[x]` 改成由命令或测试 ID 支撑的检查项，并区分汉字数、字符数、中文词数与 Markdown 字节数。

### 4. 第 18 章的手把手命令不能执行

`book/part-5/chapter-18.md:113-123` 的 `ingest` 缺少 CLI 必需的 `--output`；`--scope config/ebpf-scope.yml` 会被实现解释为 glob，而不是配置文件；`build-wiki` 和 `query` 把 `--snapshot` 指向 `generated/manifest.json`，实现实际要求快照目录。按原文运行 `build-wiki` 已实证得到 `NotADirectoryError`。

影响：违反宪章“每章命令可重复执行”。所有书中命令应进入 CI 文档测试，而不是靠人工目测。

### P1：高优先级问题

### 5. Linux 可运行能力低于目录承诺

`OUTLINE.md:83` 和 `CASE_SPEC.md:61-65` 承诺源码、文档、摘要的 BM25/向量/图混合检索，以及 Tree-sitter 与编译级精确关系比较。实际 eBPF 和全仓工具都使用正则语法候选与 BM25/SQLite FTS；查询返回相关边，但不是图检索，也没有向量通道、Tree-sitter 实现、SCIP/clang/BTF 适配器或 compiled 对照报告。

建议：要么补齐至少“BM25 + 可复现本地向量 + 有约束图扩展”的查询计划和消融测试，要么在目录与案例规格中将这些标为后续架构，不再写成已交付知识产物。

### 6. 影响分析缺少测试对象和 TESTED_BY 关系

`chapter-14.md:42` 要求 Payment、Inventory、Notification 三个消费者及对应测试，`chapter-16.md:106` 还描述沿 `TESTED_BY` 查找测试。但 `relations.json` 没有测试节点或 `TESTED_BY` 边。当前测试只验证能找到三个消费者，不能回答“会影响哪些测试”。

### 7. 许可证文件与正文描述不一致

`book/license.md:3` 称根目录 `LICENSE` 是 CC BY-NC-SA 4.0 完整法律文本；该文件实际只有 13 行摘要和 canonical URL。`LICENSE-CODE` 同样是 Apache 2.0 notice，不是完整许可证文本。公开仓库应保存官方完整文本，或把措辞改成“摘要与法律文本链接”。

### 8. 附录没有兑现目录中的评测资产

目录承诺“评测集、Rubric 与检查表”，实际附录 D 只有发布勾选表；没有可复用的 Golden Question Schema、评分 Rubric、角色/时间/证据标注模板和消融记录模板。研究索引也只是主题链接清单，不是完整书目数据库。

### 9. 引用体系尚未达到“逐声明核验”标准

50 个唯一外链在审查日均能返回成功、重定向、403 或 429 等可访问状态。对 RAG、RAPTOR、GraphRAG、MCP、Tree-sitter、SCIP、BTF 与 verifier 的抽样表明正文概括大体受原始来源支持。但链接健康只证明定位存在，不能证明每条陈述被支持。

已发现明确错误：`book/part-2/chapter-09.md:85` 将 Mem0 作者写成 “Yu Wang et al.”，原论文作者是 Prateek Chhikara、Dev Khant、Saket Aryan、Taranjeet Singh、Deshraj Yadav [4]。全书还缺作者、年份、标题、版本、访问日期统一的完整 Bibliography 和声明级 claim ledger。

### 10. “当前最新”是不可持续且已不适合书稿的表达

`SECURITY.md:5` 写“当前最新 VitePress 1.6.4”。软件版本会变化，该声明必须绑定审计日期和“本仓库锁定版本”，而不是宣称全网最新。类似动态事实应自动核验或从稳定正文移出。

### P2：结构、清晰度和工程债

1. 第 5 章没有按目录独立讲清 Late Interaction/ColBERT 和多跳检索，结构化过滤也主要散落在 ACL 描述中。
2. “语义通道”在 Northstar 实现中是确定性同义词集合 Jaccard，不是 embedding。README 虽披露这一点，但正文容易让读者把它与向量通道等同，建议统一称“离线语义代理通道”。
3. `chapter-18.md` 多处用“Tree-sitter 提供”描述最终架构，而当前实现使用正则；必须持续标注“目标架构”与“当前实现”。
4. `full_kernel.py:208` 先用 `CALL_RE` 生成 `terms`，下一行立即覆盖，是无效代码；应删除并增加空查询、特殊字符、已存在数据库、损坏数据库和中断恢复测试。
5. 全仓实验报告记录 135 万“函数候选”，远高于合理函数数量。报告已正确披露，不构成事实造假，但任何摘要都必须保留“候选”和 `syntax-only`，不能简写为函数数/调用数。
6. 当前仓库位于一个更大的脏工作树中，书项目自身没有独立 git 历史或远端发布证据。公开发布前应独立建仓，避免把父仓库无关材料带入。
7. 首页、导航和章节层级清楚，但 18 章正文没有统一的“本章目标/前置知识/可运行产物/自测题”元数据，手把手案例与理论章节之间的学习桥梁较弱。

## Synthesis & Insights / 综合判断

这些问题呈现出同一个根因：当前仓库把三种成熟度放进了同一个“完成”标签。理论框架接近可发布，教学原型可以运行，完整平台案例仍是设计稿。只要三者明确分层，这本书的可信度会明显提升；若继续使用“完整案例”“已通过”“v1.0”覆盖三者，任何一个可复现反例都会反过来削弱正确的理论主张。

第二个跨阶段主题是“检查存在，但检查对象过浅”。链接检查只验证可访问，不验证声明支持；站点 QA 只验证页面打开，不验证 Mermaid 语义；单元测试验证 ACL 与引用，却被扩张为注入、行动和完整生命周期已测。v1.0 的关键不是增加更多检查，而是让每个检查与一个明确承诺一一对应。

### 体系覆盖矩阵

| 体系层 | 理论 | 案例 | 主要缺口 |
|---|---|---|---|
| 历史与概念 | 完成 | Northstar 场景贯穿 | 历史压缩较强，缺组织变革/知识责任机制 |
| RAG 与检索 | 基本完成 | 最小 BM25 + 同义词融合 | Late Interaction、多跳、真实向量消融 |
| 层级与 Wiki | 完成 | 模板 Wiki | 人工编辑冲突、Lint 和失效没有实现测试 |
| 图谱 | 完成 | 小型 ACL 图 | TESTED_BY、跨仓、时间图与图检索缺失 |
| 记忆 | 完成 | 进程内任务列表 | 持久化、合并、遗忘、投毒测试缺失 |
| 对象/版本/时间 | 完成 | 版本字段与 URI | 双时间、删除传播、快照发布未实现 |
| 权限与安全 | 完成 | 召回前 ACL、图端点 ACL | 注入、审批、工具授权、审计闭环缺失 |
| 评测与运营 | 完成 | 20 个单元/集成测试 | 50—100 GQ、消融、延迟、成本、SLO 缺失 |
| Agent 接口与行动 | 设计完成 | JSON Context Package | REST/MCP/策略/状态机/写工具缺失 |
| 代码知识库 | 架构完整 | 真实 syntax-only 实验 | Tree-sitter/SCIP/BTF、向量、图规划与增量 |

## 验证证据

| 检查 | 结果 |
|---|---|
| VitePress 生产构建 | 通过，1.71 秒 |
| Northstar unittest | 10/10 通过 |
| Linux unittest | 10/10 通过 |
| Northstar Docker Compose | 构建并运行通过 |
| `npm audit --omit=dev` | 0 漏洞 |
| 完整开发依赖审计 | 3 个已知问题（2 moderate，1 high） |
| 唯一公开链接 | 50/50 可访问 |
| Mermaid 实际渲染 | 0/6；全部显示为代码块 |
| 第 18 章 build-wiki 命令 | 失败，`NotADirectoryError` |
| Linux v6.12 tag | annotated tag 解析到报告所写提交 `adc218676eef25575469234709c2d87185ca223a` |

## Recommendations / 发布修订门

### v1.0 必须完成

1. 决定 Northstar 是“完整案例”还是“最小纵向切片”，并让宪章、规格、正文、代码、测试和发布审计统一。
2. 若保留完整案例承诺，补齐数据规模、Golden Dataset、影响测试和一个受控写动作闭环。
3. 修复并自动执行所有书中命令。
4. 启用 Mermaid 渲染并做桌面、移动和无障碍验证。
5. 修正发布检查表、字数口径、许可证、Mem0 作者和版本措辞。
6. 对 Linux 能力做真实交付或缩小目录承诺。
7. 建立完整 Bibliography 与至少高风险声明的 claim-support ledger。
8. 独立 GitHub 仓库创建、Pages 实际部署、站点烟测和 v1.0 tag 完成后，才能把引用版本写为 v1.0。

### 可在 v1.1 继续

组织变革与知识责任人实践、更多行业案例、编译级 Linux 索引、多配置调用图、跨版本查询、真实企业数据规模基准和多语言代码仓。

## Limitations & Caveats / 方法与限制

本次采用 CEO→设计→工程→DX→事实核验的顺序。以 `BOOK_CHARTER.md`、`OUTLINE.md` 和 `CASE_SPEC.md` 为权威验收基准；读取全部项目清单与章节结构，抽查正文主张；重跑构建、20 项测试、Docker Compose、npm 审计和书中命令；检查静态 HTML；验证全部唯一公开链接；对高风险论文、规范和 Linux 官方材料做声明支持抽样；使用独立 Codex 声部进行第二遍战略审查。

本次没有逐句人工核对约 20 万 Markdown 字节的每个判断，也没有重建 3.6 GB Linux SQLite 数据库；完整 Linux 数字以保留的运行报告、固定提交和实现逻辑为证据。因此结论可判定发布门与主要事实风险，但不能宣称“每一句都已完成同行评审”。

## Bibliography / 书目

[1] Lewis, P. et al. (2020). “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” NeurIPS 2020. https://arxiv.org/abs/2005.11401 (Retrieved: 2026-08-23).

[2] Sarthi, P. et al. (2024). “RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval.” arXiv. https://arxiv.org/abs/2401.18059 (Retrieved: 2026-08-23).

[3] Edge, D. et al. (2024; revised 2025). “From Local to Global: A Graph RAG Approach to Query-Focused Summarization.” arXiv. https://arxiv.org/abs/2404.16130 (Retrieved: 2026-08-23).

[4] Chhikara, P., Khant, D., Aryan, S., Singh, T., and Yadav, D. (2025). “Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory.” arXiv. https://arxiv.org/abs/2504.19413 (Retrieved: 2026-08-23).

[5] Model Context Protocol (2026). “Specification.” https://modelcontextprotocol.io/specification/ (Retrieved: 2026-08-23).

[6] Linux Kernel Documentation (2026). “BPF Type Format (BTF).” https://docs.kernel.org/bpf/btf.html (Retrieved: 2026-08-23).

[7] Linux Kernel Documentation (2026). “eBPF verifier.” https://docs.kernel.org/bpf/verifier.html (Retrieved: 2026-08-23).

[8] Tree-sitter Contributors (2026). “Tree-sitter Introduction.” https://tree-sitter.github.io/tree-sitter/ (Retrieved: 2026-08-23).

[9] SCIP Contributors (2026). “SCIP Code Intelligence Protocol.” https://github.com/scip-code/scip (Retrieved: 2026-08-23).

[10] Torvalds, L. and Linux contributors (2024). “Linux kernel v6.12 source tag.” https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git (Verified: 2026-08-23).

## Methodology Appendix / 方法附录

审查严格顺序为 CEO、设计、工程、DX、事实核验。CEO 阶段将宪章、目录和案例规格映射到实际产物，并由兼容模型上的独立 Codex 声部复核。设计阶段检查 VitePress 配置和静态 HTML，确认导航、标题层级、移动框架与 Mermaid 输出。工程阶段重跑两组 unittest、Docker Compose、VitePress 构建和 npm 审计，并读取核心实现与测试。DX 阶段从首次读者视角抽取公开命令，实际执行第 18 章命令。事实阶段检查全部唯一公开链接，并对高风险论文、规范和官方文档做声明级抽样。

证据状态保存在同目录的 `claims.jsonl`、`evidence.jsonl`、`sources.jsonl` 与 `run_manifest.json`。`supported` 表示当前证据直接支持；`contradicted` 表示仓库中的声明与实现、测试或原始来源冲突。未进入账本的普通架构判断仍需要作者在定稿阶段负责，不能因本报告抽样通过而视为逐句认证。
