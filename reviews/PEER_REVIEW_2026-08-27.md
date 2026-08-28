# 《企业上下文》独立同行评审报告（三轮合并·终版）

审阅日期：2026-08-27（同日三轮，每轮换用不同模型独立取证）
审阅对象：`enterprise-context-book` 仓库全部内容（写作宪章、目录、案例规格、18 章正文、附录、番外、两个案例代码与数据、VitePress 站点、发布与许可材料、既有自审报告）
审阅立场：独立外部审稿人。以仓库自身的 `BOOK_CHARTER.md`、`OUTLINE.md`、`CASE_SPEC.md` 为验收合同；以实际执行的命令与仓库文件为证据。

**最终判定：不通过 v1.0 发布门。定位应为"理论初稿完整 + 教学原型可运行 + 平台案例仍是设计稿"。** 三轮判定一致收敛。

## 本文件结构与效力顺序

本文件由三轮评审按时间合并而成：**卷一**为初审全文（27 项 + 验收门 G1–G9 + 六批次执行顺序），**卷二**为第二轮复核（修正卷一 3 处、升级 1 项、新增 3 项、改写根因），**卷三**为第三轮复核（审计卷二，撤回其 P1-18 大部）。**内容冲突时效力为：卷三 > 卷二 > 卷一。** 各卷正文保持评审时原貌（含后来被修正的表述），以保留完整证据链；执行修订时以下面的《最终条目总览》为准。

## 最终条目总览（执行修订以此表为准）

| 编号 | 问题 | 详见 | 被后续轮次修订之处 |
|---|---|---|---|
| P0-1 | 字数缺口 + 参考栈缺检索/代码语义半边 | 卷一§4 | 措辞按卷二修正1；口径与单位按卷二§2；补字数策略按卷三§2.3 |
| P0-2 | 案例数据比 CASE_SPEC 小 1–2 个数量级 | 卷一§4 | — |
| P0-3 | 正文 6 处可被仓库否证的陈述（含 roles→acl） | 卷一§4 | — |
| P0-4 | "知道 vs 能做"核心主张零实现 | 卷一§4 | — |
| P0-5 | 第 18 章命令照抄必然失败 | 卷一§4 | — |
| P0-6 | 6 张 Mermaid 图未渲染 | 卷一§4 | 验收标准提高为"可访问 SVG"（卷二§5） |
| P0-7 | 七份文档发布状态互相矛盾 | 卷一§4 | 字数行是"单位替换"而非伪造（卷二§2）；审计表改行内限定（卷二修正3） |
| P0-8 | 附录 D 自检清单虚假勾选 | 卷一§4 | — |
| P0-9 | 无 Git 仓库，引用/勘误/发布模型全部悬空 | 卷一§7 | — |
| P0-10 | CI 只发布不测试，23 个测试无自动化保护 | 卷二§4 | — |
| P0-11 | 旗舰能力问题数据不可答，测试只做模型自校验（原 P1-4 升级） | 卷二§4 | — |
| P1-1 | 工程实践是全书最薄部分（15.2% vs 38.3%） | 卷一§3 | 字数缺口主体由深写本部分补足（卷三§2.3） |
| P1-2 | 理论核心六章零图示 | 卷一§3 | 须在 P0-6 之后执行 |
| P1-3 | 第 8 章体量失控 | 卷一§3 | — |
| P1-5 | 术语表仅 8 条，承重术语全缺 | 卷一§3 | certainty 改名不改值（卷二修正2） |
| P1-6 | 附录 D 无评测集与 Rubric | 卷一§3 | — |
| P1-7 | Linux 番外数字口径矛盾且不可复核 | 卷一§4 | — |
| P1-8 | Mem0/Zep 作者署名错误 | 卷一§5 | — |
| P1-9 | 引用无统一格式、无集中参考文献表 | 卷一§5 | — |
| P1-10 | 来源权威度与附录 F 承诺不符 | 卷一§5 | — |
| P1-11 | 章节骨架不统一 | 卷一§6 | — |
| P1-12 | 跨章重复度偏高 | 卷一§6 | — |
| P1-13 | 术语收尾验证（P1-5 的执行补充） | 卷一§6 | 按卷二修正2执行 |
| P1-14 | BM25 重复实现、"语义通道"名不符实、中文单字切分 | 卷一§6 | 披露动作改为"上提既有披露"（卷二修正3） |
| P1-15 | OUTLINE/CASE_SPEC 停留 v0.1 | 卷一§7 | — |
| P1-16 | LICENSE 非完整法律文本 | 卷一§7 | — |
| P1-17 | 证据分级框架提出而未贯穿 | 卷二§4 | — |
| P1-18a | 容量与性能工程整块缺失 | 卷三§2.3 | 卷二 P1-18 收窄后的唯一 P1 遗留 |
| P2-1 | SECURITY.md "当前最新"会过期 | 卷一§7 | — |
| P2-2 | research-notes.md 过短且与附录 B 重叠 | 卷一§7 | — |
| P2-3 | 成本模型的定量化例子（原 P1-18b） | 卷三§2.3 | — |
| P2-4 | 删除合规的法规命名 + 重建运维小节（原 P1-18c） | 卷三§2.3 | — |

注：卷二 P1-18 的其余五类主题缺口经卷三逐条核对**不成立**（多租户、删除级联、人在环、压缩摘要、预算约束均已有质量不低的正文），已撤回，勿按卷二 P1-18 原文执行。

## 最终执行批次（合并三卷修订后的定稿顺序）

- **批次 0 基础设施**：P0-9（Git 初始化+清 `__pycache__`+tag）；P0-6（Mermaid → 可访问 SVG）；P1-16（许可证全文）。
- **批次 1 诚实性对齐**：P0-3；P0-7（含 `BOOK_CHARTER.md:72` 钉死字数口径、落盘 `scripts/wordcount.py`、修测试计数 10→13）；P0-8；P1-7；P1-15；P2-1；产出 `reviews/TEST_PLAN_STATUS.md`（把 `TEST_PLAN_2026-08-23.md` 逐条映射到门 G1–G9，初始几乎全为"未实现"——这就是修订主清单）。
- **批次 2 工程真实性**：P0-4；P0-2；P0-10（CI 增加 test job 并前置于 build）；P0-11（数据↔领域模型契约测试+补齐关系数据）；P1-14；P1-13。
- **批次 3 评测资产**：P1-6；Golden Questions 50–100 及回归；注入/写闭环/幂等三类测试。
- **批次 4 内容与结构**：P1-12（回收 2,000–3,000 字重复）；P1-1 与 P0-1（字数缺口主体 = 深写第四部分工程实践，把批次 2/3 的真实实现转写为正文）；P1-3；P1-2；P1-18a（容量与性能工程一节，2,500–3,500 字）。
- **批次 5 引用与形式**：P1-8；P1-9；P1-10；P1-5；P1-11；P1-17；P2-2；P2-3；P2-4。
- **批次 6 复核与发布**：G1–G9 全过；`TEST_PLAN_STATUS.md` 全部"已实现/不适用"；重写 `RELEASE_AUDIT.md`（三态+验证方式）；`run_manifest.json` verdict 改 `cleared`；升 `1.0.0` 并打 tag——此时全书方可出现"v1.0"字样。

---

# 卷一 · 初审报告（第一轮）

> 本卷 27 项中：P0-1 的措辞、certainty 字段类型、降级披露三处判断已被卷二修正；P1-4 已升级为 P0-11（正文见卷二）；第 9 节执行顺序已被上方《最终执行批次》取代。本卷其余内容（含全部定位、证据、替换文本与 G1–G9 验收门）均有效。

## 0. 如何使用本报告（写给执行修订的模型）

**执行约定**

1. 本报告每条问题的格式固定为：`问题编号｜定位｜证据｜判断｜修改动作`。只有"修改动作"是需要落盘的内容，其余三项是判断依据，不要写进书稿。
2. 定位使用 `文件:行号` 或 `文件 §小节`。行号以 2026-08-27 的仓库状态为准；若修订过程中行号漂移，用小节标题重新定位，不要按行号盲改。
3. 凡标注"给出替换文本"的条目，直接使用报告中提供的文本，不要重写措辞——这些文本已经过与代码/数据的一致性核对。
4. 凡涉及"删承诺"与"补实现"二选一的条目，报告给出了推荐路线与代价。若时间受限，一律走"删承诺"路线：**把不存在的能力从正文移到"后续架构"，比留着一句无法复现的断言更能保住全书可信度。**
5. 每完成一批修订，运行第 8 节给出的验收命令，不要靠目测。
6. 不要删除 `reviews/` 下的既有报告。它们是审阅链路的一部分。

**优先级定义**

- **P0**：阻断发布。包含"书里写了但仓库里没有"的可核验假陈述、自相矛盾的规范性文档、读者照抄会失败的命令。
- **P1**：影响本书核心价值（体系性与工程实践）的结构性缺陷，v1.0 应完成。
- **P2**：一致性、体例、可读性与工程债，可在 v1.0 收尾或 v1.1 处理。

**与既有自审报告的关系**

仓库已存在 `reviews/COMPLETE_REVIEW_2026-08-23.md`，质量相当高，方向判断正确。本报告不重复它的论证，而是做三件事：**（a）复核它的 12 条结论今天是否已修（结论：一条未修，见第 2 节）；（b）补充它未覆盖的量化事实与新缺陷（第 3–7 节）；（c）把全部结论转成可被模型逐条执行的修订指令（第 8、9 节）。** 本报告共 27 项：P0 九项、P1 十六项、P2 两项。若两份报告冲突，以本报告为准，因为本报告基于 2026-08-27 的实际文件状态重新取证。

---

## 1. 总体结论

### 1.1 这本书做对了什么（修订时必须保护的部分）

先说不该动的地方，因为下面的批评很密集，容易让修订者把好东西一起改掉。

这本书真正的贡献是**一套自洽的边界划分**：把"知识 / 记忆 / 实时状态 / 工具 / 任务上下文"拆开而不混谈；坚持"召回前鉴权"而不是检索后过滤；坚持"派生物可删除可重建、原始来源才是证据"；坚持"知道"与"能做"分权治理；坚持把评测、版本、时间、血缘、安全当作一等公民而不是附加功能。这些判断在第 10—13 章形成了全书最稳定的骨架，第 3 章的类型学、第 11 章的对象信封、第 12 章的行动边界是可以直接被工业界引用的。

Linux 番外的自我批评也值得保留：它主动披露"135 万函数候选偏高，说明正则把宏误判为函数"、"3.6 GB 索引对长期知识库不可接受"、"`if` 出现在首屏"。**在一本 AI 参与撰写的技术书里，主动暴露误差比展示漂亮结果稀缺得多。修订时不要为了好看删掉这些段落。**

### 1.2 不能通过的三条根因

**根因一：三种成熟度共用一个"完成"标签。** 理论部分接近可发布，教学原型确实能跑，而"完整企业平台案例"仍然只是设计稿。当同一份仓库用"完整案例""已通过""v1.0"同时覆盖三者时，任何一个可复现的反例都会反过来削弱本来正确的理论主张。这条与既有自审报告一致，但本报告给出了量化边界（第 4 节）。

**根因二：体量与结构与承诺不匹配，且工程实践部分最薄。** 全书正文汉字 54,446 个（剔除代码块，含番外与附录），是 `BOOK_CHARTER.md:72` 承诺下限 8 万字的 **68.1%**。更关键的是薄的地方错了：第四部分"Northstar 实践"四章共 8,296 字，占全书 15.2%；而第二部分六章理论 20,838 字，占 38.3%。用户对本书的期望是"体系化知识 + 工程实践"，当前形态是"体系化知识 + 工程实践的目录"。

**根因三：仓库缺少单一真相源，七份规范性文档给出互相冲突的完成度判断。**

| 文件 | 对"是否可发布"的表态 |
|---|---|
| `BOOK_CHARTER.md:70-79` | 定义 8 项完成标准 |
| `RELEASE_AUDIT.md:5-15` | 9 项全部"通过"/"候选就绪" |
| `reviews/COMPLETE_REVIEW_2026-08-23.md` | `DONE_WITH_CONCERNS，v1.0 NOT CLEARED`，综合 6.2/10 |
| `reviews/run_manifest.json` | `"verdict": "not-cleared"` |
| `CHANGELOG.md` | 已发布 `1.0.0-rc.1`，同时"待发布"里列着已经在正文中的第 8 章扩写 |
| `package.json` | `"version": "1.0.0-rc.1"` |
| `book/license.md:11` | 建议引用格式写 `v1.0, 2026` |

这不是文档冗余，而是治理缺陷：**一本讲"知识必须有权威来源、版本和血缘"的书，自身的发布状态没有权威来源、版本和血缘。** 这一条应当被当作全书第一位的修订项，因为它是所有其他不一致的上游。

---

## 2. 对既有自审报告的复核（2026-08-23 → 2026-08-27）

结论：**核心问题一条都没有修。** 期间唯一的仓库变化是站点重新构建（`book/.vitepress/dist` 时间戳 2026-08-25）、`.gitignore` 已存在、Northstar 测试从 10 个增加到 13 个。

| 旧编号 | 问题 | 今日复核结果 | 证据 |
|---|---|---|---|
| 旧-1 | Northstar 交付不符合 `CASE_SPEC` | **未修** | `data/` 全部 JSON 合计 7,476 字节；`knowledge.json` 仍为 8 个对象 |
| 旧-2 | 证据到行动闭环未实现 | **未修** | `src/northstar.py` 共 230 行，`grep` 无 `prepare_replay`/`approval`/`state_machine`/`idempotency` |
| 旧-3 | 附录发布检查表存在虚假勾选 | **未修** | `book/appendices.md:40-47` 八项仍全为 `[x]` |
| 旧-4 | 第 18 章命令不可执行 | **未修** | `linux_kb/__main__.py:15-24` 的参数定义与 `chapter-18.md` §18.9 仍不匹配 |
| 旧-5 | Linux 能力低于目录承诺 | **未修** | 无 Tree-sitter/SCIP/clang/BTF 适配器，无向量通道 |
| 旧-6 | 影响分析缺 `TESTED_BY` | **未修** | `relations.json` 仍只有 5 条边，无 Test 节点 |
| 旧-7 | LICENSE 不是完整法律文本 | **未修** | `LICENSE` 13 行、`LICENSE-CODE` 16 行 |
| 旧-8 | 附录未兑现评测资产 | **未修** | 附录 D 仍只有发布勾选表 |
| 旧-9 | 引用未达逐声明核验；Mem0 作者错误 | **未修** | `part-2/chapter-09.md:85` 仍写 `Yu Wang et al.` |
| 旧-10 | "当前最新 VitePress" 动态表述 | **未修** | `SECURITY.md` 第 2 段原文未改 |
| 旧-P2-4 | `full_kernel.py` 无效代码 | **未修** | `full_kernel.py:209-210`，`terms` 被赋值后立即覆盖 |
| 旧-验证项 | 6 个 Mermaid 图未渲染 | **未修** | `dist/` 中 5 个 HTML 与 5 个 JS chunk 仍含 `language-mermaid` |

**修改动作（贯穿全局）**：把 `reviews/COMPLETE_REVIEW_2026-08-23.md` 的 P0/P1 列表转成 `TODO.md` 或 GitHub Issue 清单并逐条关闭，而不是让它以"报告"形态停留在仓库里。一份未被消费的审查报告，和没有审查是等价的。

---

## 3. 体系性问题（结构层）

用户对本书的第一个期望是"体系化讲述企业上下文相关知识"。体系性目前的缺陷不在骨架，而在**骨架的密度分布、自反一致性和收口**。

### P1-1｜结构重心与本书目的相反：工程实践是全书最薄的部分

**定位**：`book/part-4/`（ch14–17）整体；对照 `book/part-2/`（ch04–09）
**证据**（剔除代码块的汉字数）：

| 部分 | 章节 | 汉字 | 占比 | 图 | 代码块 |
|---|---|---|---|---|---|
| 一 认识企业上下文 | ch01–03 | 6,644 | 12.2% | 3 | 4 |
| 二 核心知识能力 | ch04–09 | 20,838 | 38.3% | 0 | 1 |
| 三 平台架构与治理 | ch10–13 | 10,962 | 20.1% | 3 | 5 |
| 四 Northstar 实践 | ch14–17 | 8,296 | 15.2% | 0 | 14 |
| 五 大型代码库实践 | ch18 + 番外 | 6,117 | 11.2% | 0 | 4 |
| 附录/首页/索引/许可 | — | 1,589 | 2.9% | 0 | 0 |
| **合计** | 22 文件 | **54,446** | 100% | **6** | **28** |

**判断**：一本以"工程实践"为卖点的书，把 38% 的篇幅给了理论综述，只给动手部分 15%，且四章实践里最薄的一章（ch14，1,920 字）恰好是本该定义整个案例世界的那一章。ch15–17 的写法是"应该怎样做"的规格陈述，而不是"我做了，这是输出，这是我踩的坑"。全书唯一真正带着失败与误差写作的是 Linux 番外——那才是工程实践该有的质感。

> 表注：「图」列统计 `mermaid` 代码块，它同时被计入「代码块」列。因此非图示代码块为：一部 1、二部 1、三部 2、四部 14、五部 4。第二部分六章共 20,838 字，只有 1 个代码块、0 张图。

**修改动作**：

1. 把补写预算的 **60% 以上投给第四、第五部分**，而不是均摊。目标配比调整为：一部 12%、二部 30%、三部 20%、四部 26%、五部 12%。按 8.5 万字总量计算，第四部分应从 8,296 字扩到约 22,000 字。
2. ch14–17 每章必须新增以下四类**只能来自真实执行**的内容，每类至少一处：
   - **真实终端输出**：粘贴 `python3 src/northstar.py ...` 的实际 JSON 输出（截断可以，但必须是真实运行结果，字段名与代码一致）。
   - **一次失败与修复过程**：ch15 §15.8 已有一个（泛化自然语言导致政策压过代码），这是全书最好的工程段落之一，把它作为模板，在 ch16、ch17 各补一个（建议：ch16 补"确定性边与推断边混用导致影响面虚高"；ch17 补"审批令牌绑定参数散列后，预览与执行之间队列变化导致确认失效"）。
   - **规模与代价数字**：即使是 fixture 规模，也要给出对象数、边数、索引体积、查询耗时、Token 占用。当前四章没有任何一个可度量数字，这是"实践"读起来像"规格"的直接原因。
   - **迁移步骤的目录 diff**：ch15 §15.4 说"迁移到 PostgreSQL"却只给了一张建表语句。补一段"从 JSON 切到 PostgreSQL 后，`src/` 与 `tests/` 各新增/修改了哪些文件"，哪怕以清单形式。
3. ch14 是最需要扩写的一章。它当前用 1,920 字承担"定义整个案例世界"的职责，导致后三章不断重复解释同一批角色和对象。建议扩到 3,500 字并补入：五个逻辑服务的实际目录结构、事件流时序图（Mermaid）、四类角色的完整权限矩阵表格（当前是散文描述）、两条任务链的输入输出示例。

### P1-2｜全书理论核心（第二部分）零图示

**定位**：`book/part-2/chapter-04.md` — `chapter-09.md`
**证据**：六章共 20,838 字，`mermaid` 块 0 个，代码块 1 个（ch08 内的一段 JSON）。全书仅 6 张图，全部集中在 ch01/02/03/10/13。
**判断**：第二部分承载的正是最需要图示的内容——RAG 管线阶段、父子分块结构、RRF 融合流程、RAPTOR/PageIndex 的层级形态、概念/逻辑/物理三层模型、知识图谱与 GraphRAG 的关系、记忆主体的作用域嵌套。这些结构用纯散文表达，读者必须自行在脑中重建拓扑。这是"体系化"打折最严重的地方：**体系是有结构的，而结构没有被画出来。**
**修改动作**：为第二部分补 **8 张 Mermaid 图**，每章至少一张，建议如下（图必须与正文小节一一对应，不要另起概念）：

| 位置 | 图类型 | 内容 |
|---|---|---|
| ch04 §4.1 后 | `flowchart LR` | 连接器 → 解析 → 分块 → 索引 → 查询 → 生成，并标出每一步产出的对象与失败模式 |
| ch04 §4.3 后 | `flowchart TB` | 父子分块：叶子块命中 → 回溯父块 → 引用仍指向叶子版本 |
| ch05 §5.2 后 | `flowchart LR` | 双通道 + RRF 融合 + 交叉编码器重排 + 降级回退路径 |
| ch06 §6.2 后 | `graph TD` | 来源结构层级 vs 生成结构层级（RAPTOR / PageIndex）并置对照 |
| ch07 §7.2 后 | `flowchart LR` | Raw Sources → Ingest → Query → Lint 闭环，标出 staleness 传播方向 |
| ch08 §8.3 后 | `graph TB` | 词汇 → 分类法 → 数据 Schema → 本体 → 知识图谱的能力递进 |
| ch08 §8.5 后 | `graph LR` | 概念层 / 逻辑层 / 物理层三层投影关系 |
| ch09 §9.2 后 | `graph TB` | 记忆主体作用域：会话 ⊂ 任务 ⊂ 用户 / Agent / 组织，标注写入门与晋升路径 |

注意：这一条与 P0-4（Mermaid 未渲染）绑定。**在 Mermaid 渲染修好之前不要新增 Mermaid 块**，否则只是把 6 个未渲染代码块变成 14 个。

### P1-3｜第 8 章体量失控，破坏全书节奏

**定位**：`book/part-2/chapter-08.md`（5,816 字，159 行）
**证据**：全书平均每章 2,562 字，ch08 是平均值的 2.27 倍，是最短章节 ch14（1,920 字）的 3.03 倍。`CHANGELOG.md` 的"待发布"里还写着"将第 8 章扩展为知识建模、本体与图谱的系统方法"——说明这一章是后期加塞扩写的，且扩写完成后没有回写变更记录。
**判断**：ch08 现在实际包含四个独立主题：知识建模方法论、语义网标准族（SKOS/OWL/RDF/SHACL）、三层模型与能力问题、知识图谱与 GraphRAG。这四个主题的读者需求不同，混在一章会让第二部分的阅读曲线突然陡起。
**修改动作**（二选一，推荐方案 A）：

- **方案 A（推荐）**：拆为两章，全书变为 19 章——仍在 `BOOK_CHARTER.md:72` 承诺的"14–18 章"之外，因此需同步把宪章改为"14–20 章"，并更新 `OUTLINE.md`、`book/.vitepress/config.mts` 侧边栏、所有跨章引用。拆分线：
  - 新 ch08《知识建模与本体：从词汇到可约束的语义》= 现 §8.1–§8.5 + SKOS/OWL/SHACL/三层模型/能力问题
  - 新 ch09《知识图谱与图检索》= 现 §8.6 以后 + GraphRAG + 代码图 + 时序图 + 证据等级，原 ch09（智能体记忆）顺延为 ch10
- **方案 B**：保持 18 章，把 ch08 中的标准族细节（SKOS/OWL/RDF/SHACL 的条款级说明）下移到新增附录 H《语义网标准族速查》，正文只保留"什么时候需要哪一层"的决策路径，把 ch08 压到 3,500 字以内。

### P1-4｜体系存在自反矛盾：本书的规范模型被本书的示例数据违反

这是**体系性问题中最严重的一条**，也是既有自审报告没有覆盖的新发现。本书反复主张"派生知识必须带信封、时间、血缘与证据等级"，然后用一套不带这些字段的数据来演示它。

**证据 A：对象信封缺失**

- 规范：`book/part-3/chapter-11.md:24-44` 给出强制信封，字段含 `version_id`、`source`、`time.valid_from`、`time.valid_to`、`time.observed_at`、`lineage.derived_from`、`lineage.transform`、`content_hash`；`part-2/chapter-04.md:23` 进一步称"缺少这组时间语义，系统很容易用今天采集到的旧制度回答昨天或明天的问题"。
- 实际：`examples/enterprise-case/data/knowledge.json` 的 8 个对象只有 `acl`、`authority`、`citation`、`id`、`kind`、`system`、`tenant`、`text`、`title`、`version` 十个键。**`valid_from`、`valid_to`、`observed_at`、`lineage`、`content_hash`、`version_id` 六个字段一个都没有。**
- 后果：ch14 §14.3 第 4 条验收任务"当前政策与历史 ADR 冲突时，按时间和权威来源判断"在当前数据上**不可能实现**，因为数据里没有时间。ch13 与 ch16 描述的"历史时间题型"同理。

**证据 B：领域模型与关系数据互不相干**

- `examples/enterprise-case/data/domain-model.json` 声明的关系类型是 `CALLS`、`IMPLEMENTS`、`ON_CALL_FOR`、`DOCUMENTED_BY`、`GOVERNED_BY`，并为每种关系定义了 `allowedEvidence`。
- `examples/enterprise-case/data/relations.json` 实际使用的类型是 `CONSUMED_BY`、`AFFECTED`、`DOCUMENTED_BY`。**五种声明类型里只有 `DOCUMENTED_BY` 被实际使用；实际使用的 `CONSUMED_BY` 和 `AFFECTED` 两种未被声明。**
- `examples/enterprise-case/tests/test_domain_model.py` 的三个测试（`test_competency_questions_reference_declared_relations`、`test_relations_reference_declared_entity_types`、`test_temporal_relations_are_explicit`）**只校验 `domain-model.json` 自身的内部自洽，从不把它与 `relations.json` 交叉校验**。所以这个"机器可读领域模型"是一个不约束任何东西的装饰品。
- 后果：这正是 ch08 与 ch18 §18.10 反复警告的失效模式——"图谱伪装成完整真相""覆盖率不能把候选边计作精确边"。书里批判的错误，书自己的案例正在犯。

**证据 C：Snapshot Manifest 是一个硬编码字符串**

- 规范：`chapter-10.md` 与 `chapter-11.md` 把 Snapshot Manifest 定义为"多类索引共同指向的一致知识版本"（亦见 `appendices.md:11` 术语表）。ch15 §15.9 要求"候选索引完成后运行回归，通过后生成 Snapshot Manifest，并原子切换在线别名"。
- 实际：`src/northstar.py` 中 `"manifest": "northstar-fixture-v1"` 是写死的字符串常量，不由任何索引内容计算得出；`"degraded_channels": []` 恒为空列表，没有任何代码路径能把它置为非空，而 ch15 §15.6 与 ch17 §17.1 都把降级标记当作核心契约。

**修改动作（P1-4 整体，按此顺序执行）**：

1. **改数据，不改书**。这是唯一正确的方向：书里的规范是对的，数据是错的。为 `knowledge.json` 的全部 8 个对象补齐信封字段。示例（以退款政策对象为模板，其余照此扩展）：

```json
{
  "id": "policy-refund-window",
  "version_id": "kv:sha256:3f1c...",
  "kind": "policy",
  "tenant": "northstar",
  "title": "EMEA 退款时限政策",
  "text": "...",
  "acl": ["support", "developer", "incident_commander", "external"],
  "authority": "policy_owner",
  "citation": "knowledge://northstar/policy/refund-window@v3#emea",
  "source": {"uri": "data/sources/policy/refund-window.md", "revision": "v3"},
  "time": {"valid_from": "2026-07-01T00:00:00Z", "valid_to": null, "observed_at": "2026-07-01T02:11:00Z"},
  "lineage": {"derived_from": ["data/sources/policy/refund-window.md"], "transform": "markdown-parser@1"},
  "content_hash": "sha256:3f1c..."
}
```

2. 至少加入**一对时间冲突对象**（同一 `id` 的 `@v2` 与 `@v3`，`valid_to` / `valid_from` 相接），否则 ch14 §14.3 第 4 条验收任务和 ch13 的历史时间题型永远无法演示。
3. 让 `domain-model.json` 与 `relations.json` 对齐：把 `CONSUMED_BY`、`AFFECTED` 补入声明并给出 `allowedEvidence`；删除或实际使用 `CALLS`、`IMPLEMENTS`、`ON_CALL_FOR`、`GOVERNED_BY`。
4. **新增一个交叉校验测试**（这是本条最重要的落地物），文件 `tests/test_domain_model.py`，测试名建议 `test_every_relation_edge_conforms_to_declared_model`：断言 `relations.json` 中每条边的 `type` 出现在 `domain-model.json` 的声明中、两端实体类型符合声明的主客体类型、`certainty` 值在声明的 `allowedEvidence` 集合内。**没有这个测试，第 3 步随时会再次漂移。**
5. 让 `manifest` 由内容计算：`manifest = "northstar-" + sha256(所有对象 content_hash 排序拼接)[:12]`，并新增测试断言"修改任一 fixture 后 manifest 值变化"。这是全书"快照可重放"主张的最小可信实现，成本约 10 行代码。
6. 让 `degraded_channels` 真的能非空：给 `search()` 增加一个 `disabled_channels` 参数（或读环境变量），当语义通道被关闭时把 `"semantic"` 写入 `degraded_channels`，并加测试。这同时为 ch15 §15.6、ch17 §17.1、ch13 的降级叙述提供了可执行证据。

### P1-5｜术语表只有 8 条，缺的正是本书自创且承重的术语

**定位**：`book/appendices.md:3-12`
**证据**：附录 A 收录 8 条（企业上下文、知识库、记忆、原始来源、派生知识、Provenance、Snapshot、Context Pack）。而全书反复使用且承担论证重量的以下术语**全部缺席**：ArtifactFS、Snapshot Manifest、编译 Wiki、Context API、Context Package、证据等级（deterministic / resolved / asserted / heuristic / inferred）、双时间（valid time / system time）、知识候选（knowledge_candidate）、任务记忆主体、降级通道、权威来源、召回前鉴权、语义代理通道。

**证据（术语定义位置错乱）**：`ArtifactFS` 首次出现在 `part-2/chapter-05.md:51`，但唯一的定义出现在 `part-5/chapter-18.md` §18.5（"ArtifactFS 是这里对版本化源码工件层的抽象"）。读者在第 5 章遇到它时，要跳过 13 章才能知道它是什么，而且"这里"一词暗示它只是该节的局部说法，实际上它在 ch05、ch15、ch16、ch18、番外五处被当作正式组件使用。
**判断**：术语表规模与全书术语密度严重不匹配。对一本试图**建立领域词汇**的书来说，术语表就是它的交付物之一，不是附属清单。
**修改动作**：

1. 附录 A 扩到不少于 30 条，每条格式统一为「术语（英文）：一句定义。首次出现：第 N 章 §N.M。」并在正文首次出现处加锚链接回附录。
2. 把 `ArtifactFS` 的定义**上移到 `chapter-05.md:51` 首次出现处**（一句话即可："本书用 ArtifactFS 指代版本化源码工件层：按仓库与提交保存不可变 blob，并提供路径、行号与内容散列；它可以由本地 Git 对象库、对象存储或源码归档实现。"），ch18 §18.5 保留展开说明并改为回指。
3. 统一 `Context Pack` / `Context Package`：`appendices.md:12` 用「Context Pack」，`part-4/chapter-17.md` §17.2 用「Context Package」，两者指同一物。**统一为 `Context Package`**（因为它是 API 响应体的名字，与 `Context API` 成对），附录 A 同步改名。
4. 统一证据等级词表。当前存在三套：`chapter-08.md` 的五级（deterministic / resolved / asserted / heuristic / inferred）、`chapter-16.md` §16.1 的三级（resolved / heuristic / inferred）、JSON 数据里的字段名 `certainty`。**以 ch08 的五级为规范**，ch16 改为"本章只用到其中三级"，并把数据字段统一命名为 `evidence_tier`（或保留 `certainty` 但在 ch08 明确二者是同一概念的字段名）。目前读者无法判断三套是否等价。

### P1-6｜附录 D 名不符实，评测资产整体缺失

**定位**：`book/appendices.md:38-47`，对照 `OUTLINE.md:90`
**证据**：`OUTLINE.md:90` 承诺附录 D 为"评测集、Rubric 与检查表"，交付的附录 D 只有一张 8 行的发布勾选表，没有评测集、没有 Rubric。同时 `OUTLINE.md:87-92` 列出附录 A–F，实际交付 A–G，且 F 的内容已换成"研究与引用方法"（原承诺的"许可证、引用与贡献方式"被移到 `book/license.md` 与 `CONTRIBUTING.md`）。
**判断**：全书第 13 章用 2,669 字论证"Golden Dataset 是评测的最小单元"，却没有交付一个可复用的标注模板。这是"体系化"最后一公里的断裂：读者读完知道该建评测集，但没有任何可直接拿走的东西。
**修改动作**：把附录 D 重构为四个子节，并把 `OUTLINE.md:87-92` 的附录清单同步改为 A–G 的实际交付：

- **D.1 Golden Question Schema**：直接复用 `chapter-14.md` §14.6 的 JSON 结构，但补齐 `bucket`、`difficulty`、`expected_refusal`、`expected_conflict`、`annotator`、`annotated_at`、`snapshot` 字段，并给出字段级说明表。
- **D.2 答案评分 Rubric**：给出 4 个维度 × 4 级评分表（证据充分性 / 引用精确性 / 结论正确性 / 边界声明），每级配一句判定标准。这是当前全书完全缺失的东西。
- **D.3 消融记录模板**：表头为「通道组合 / 题型 / Recall@K / MRR / nDCG@10 / 引用精确率 / P95 延迟 / 结论」，附一行填写示例。
- **D.4 发布检查表**：保留现有 8 条，但每条后面必须挂一个可执行的验证命令或测试 ID（见本报告第 8 节），并按第 4 节 P0-3 的要求修正虚假勾选。

---

## 4. 阻断发布的问题（案例代码、示例命令与发布材料）

用户对本书的第二个期望是"包含一些工程实践"。这一节是本报告最重的部分，因为**当前的工程实践部分不是质量不足，而是承诺与交付之间存在一到两个数量级的差距**，且差距被发布文档标记为"通过"。

### P0-1｜承诺的参考技术栈几乎全部未出现，"平台"实际是 301 行标准库脚本

**定位**：`BOOK_CHARTER.md:62`；`examples/enterprise-case/src/`
**证据**：

| 宪章 §8 承诺的组件 | 仓库中的实际状态 |
|---|---|
| Python | ✅ 有（标准库，无第三方依赖） |
| PostgreSQL / pgvector | ❌ 完全不存在，仅在 ch15 §15.4 有一段 `CREATE TABLE` 示意 |
| 轻量图 | ⚠️ `relations.json`（5 条边）+ `northstar.py` 里的 BFS |
| Tree-sitter | ❌ 完全不存在，Linux 案例用正则 |
| SCIP | ❌ 完全不存在 |
| Markdown | ✅ 有 |
| MCP / REST | ❌ 完全不存在，无任何服务端代码 |
| Docker Compose | ✅ 有（两个一次性容器） |
| GitHub Actions | ✅ 有 `.github/workflows/docs.yml` |
| VitePress | ✅ 有 |

`src/northstar.py` 230 行 + `src/context_demo.py` 71 行 = **301 行**，数据 `data/*.json` 合计 **7,476 字节**。这就是全书四章 Northstar 实践的全部可执行产物。
**判断**：`RELEASE_AUDIT.md:9` 把这一项标为"通过"，理由是"标准库纵向切片、Docker Compose、10 项自动测试"。但宪章要求的是一个能被替换的参考栈，不是一个纵向切片。**"纵向切片"是一个正确且诚实的定位；把它标为"通过"宪章 §8 则不是。**
**修改动作**（推荐路线：改承诺，而不是补实现）：

1. 把 `BOOK_CHARTER.md:62` 改为两句话，明确区分"书中论述的参考栈"与"仓库交付的最小实现"：

> 正文保持厂商中立；论述中的参考实现栈为 Python、PostgreSQL/pgvector、轻量图、Tree-sitter、SCIP、Markdown、MCP/REST、Docker Compose、GitHub Actions 和 VitePress，组件必须有清晰替换边界。**本仓库交付的可执行产物是该栈的最小纵向切片：Python 标准库实现对象、ACL、版本化引用、BM25 与离线语义代理通道、确定性图遍历与模板 Wiki；PostgreSQL/pgvector、Tree-sitter、SCIP 与 MCP/REST 在正文中作为目标架构描述，不包含在本仓库的可运行代码中。**

2. 在 `examples/enterprise-case/README.md` 顶部加一张与上表同构的"承诺 vs 交付"矩阵，让读者第一眼就知道边界。这一张表能挽回的可信度，比补 1000 行代码更多。
3. `RELEASE_AUDIT.md:9` 的结论从"通过"改为"部分交付（最小纵向切片）"，并在"已知边界"里补一条。

### P0-2｜案例数据规模比 `CASE_SPEC.md` 承诺小一到两个数量级

**定位**：`CASE_SPEC.md:15-22`（亦被 `chapter-14.md` §14.2 逐条复述）；`examples/enterprise-case/data/`
**证据**：

| 规格承诺 | 实际交付 | 缺口 |
|---|---|---|
| 5 个逻辑代码仓及构建、测试、提交版本 | 3 个 `kind:"code"` 的知识对象 | 无仓库结构 |
| 6–10 份 ADR | 1 份 | −5 至 −9 |
| 8–12 份 Runbook / 事故复盘 / 工单 | 1 份 Runbook + 1 份 incident | −6 至 −10 |
| OpenAPI、事件 Schema、部署与监控配置 | 1 个 `kind:"schema"` 对象 | 无 OpenAPI / 无部署配置 |
| 服务目录、团队所有权、值班信息 | 无独立对象 | 全缺 |
| 脱敏订单、队列指标、任务历史 fixture | `runtime.json` 1 个资源 | 无订单、无任务历史 |
| 3–4 类角色及 ACL | ✅ 4 类角色 + 第二租户 | 达成 |
| **50–100 条 Golden Questions** | **0 条** | **−50 至 −100** |
| Docker Compose 一键启动 | ✅ 达成 | 达成 |

**判断**：Golden Questions 为零是最严重的一项，因为它同时使 ch13、ch14 §14.6、ch16 §16.8、ch17 §17.9 的评测叙述全部失去可执行落点，也使 `TEST_PLAN_2026-08-23.md` 的"数据规格数量门"无法通过。
**修改动作**（这是本报告唯一建议"补实现而非删承诺"的地方，理由见下）：

1. **必须新增 `examples/enterprise-case/data/golden-questions.json`，不少于 24 条**。理由：Golden Dataset 是全书评测论证的最小单元，一条都没有意味着第 13 章是纯理论；而 24 条是覆盖 ch14 §14.6 声明的 9 个分桶（精确定位、语义解释、跨来源综合、关系影响、历史时间、权限隔离、拒答、提示注入、行动审批）× 每桶至少 2 条简单 + 1 条困难的下限。补 24 条的成本约等于写 400 行 JSON，远低于它带来的可信度。
2. 同步新增 `tests/test_golden_questions.py`，逐题断言：必要证据全部命中、禁止证据一条不出现、`principal` 不同则结果集不同、缺参数题返回澄清而非猜测、注入题不改变工具可见性。**测试数量应等于题目数量**，这样第 13 章"每条样本绑定固定数据快照与必要证据"才成立。
3. 数据规模按"够用即止"补齐，不必凑满规格上限。建议的最小补齐量：ADR 3 份（含 1 份与当前政策冲突的历史 ADR，用于时间冲突题）、Runbook 3 份（含 1 份限制 ACL 的安全事故手册，用于权限隔离题）、事件 Schema 2 版（`order.cancelled@v1` / `@v2`，用于影响分析与不兼容变更题）、服务目录 1 份（5 个服务 + 团队 + 值班，用于所有权题）、测试对象 3 个（用于 `TESTED_BY` 题，见 P0-6）。
4. 补齐后**同步收窄 `CASE_SPEC.md:15-22` 的数字**到实际交付量，并把标题从"v0.1"改为与发布版本一致。规格文件永远不应该比交付物更宏大。

### P0-3｜正文中存在可被仓库直接否证的事实陈述（共 6 处）

这一类问题最伤全书：读者只要打开 `examples/` 就能验证书在说假话。逐条列出，全部需要改。

| 编号 | 定位 | 书中原文 | 仓库事实 | 修改动作 |
|---|---|---|---|---|
| a | `chapter-13.md` §13.9 | "Northstar 为退款场景建立 60 条初始样本，覆盖政策解释、错误码、跨文档综合、代码定位、影响路径、历史时间、角色隔离、提示注入和工具审批。每条样本绑定固定数据快照与必要证据。" | 仓库 Golden Questions 数量为 **0** | 若执行 P0-2 补到 24 条，改为"建立 24 条初始样本"并保留分桶列表；若不补，整段改为将来时的方法说明："退款场景的初始样本应覆盖……"，并明确"本仓库尚未提供公开题集" |
| b | `chapter-14.md` §14.2 | 数据集清单第 9 项"50—100 条 Golden Questions 和必要证据" | 同上 | 与 `CASE_SPEC.md` 同步改为实际交付量 |
| c | `chapter-16.md` §16.8 | "图沿 `CONSUMED_BY` 找到三个处理符号……沿 `TESTED_BY` 和 `DOCUMENTED_BY` 找到测试与 Runbook" | `relations.json` 无 `TESTED_BY` 边、无 Test 节点 | 优先补数据（3 个测试对象 + 3 条 `TESTED_BY` 边，成本极低）；否则删掉 `TESTED_BY` 的部分 |
| d | `chapter-15.md` §15.1 | 数据对象示例使用 `"roles": ["developer", "incident_commander"]` | 实际数据与代码用的键是 `acl`（`context_demo.py:44` 为 `doc["acl"]`） | 把示例里的 `roles` 改为 `acl`。这是读者照着示例改数据会直接踩的坑 |
| e | `chapter-15.md` §15.1 | 同一示例的 `"citation": "code://northstar/payment@c1/handlers.py#handle_order_cancelled"`，正文称"每个结果都返回稳定引用""引用可回跳" | `context_demo.py:53` 恒定构造 `f"knowledge://northstar/{doc['id']}@{doc['version']}"`，**完全忽略数据里的 `citation` 字段**，实际输出是 `knowledge://northstar/code-refund-consumer@commit:abc123`，无法回跳到文件与符号 | 改代码而非改书：`context_demo.py:53` 改为 `doc.get("citation") or f"knowledge://northstar/{doc['id']}@{doc['version']}"`，并加测试断言代码类对象的引用以 `code://` 开头。这是 4 行改动，却直接决定"可回跳引用"这个核心主张是否成立 |
| f | `chapter-17.md` §17.2 | Context Package 响应示例含 `allowed_tools`、`conflicts`、`degraded_channels` 等字段 | `northstar.py` 的 `context()` 返回体中 `degraded_channels` 恒为 `[]`，`allowed_tools` 无任何实现来源 | 见 P1-4 修改动作 6；`allowed_tools` 至少实现为"按角色查表返回四个只读能力名"，否则在示例上标注"字段已定义，本仓库未实现" |

### P0-4｜"知道 vs 能做"这一核心差异化主张零实现

**定位**：`chapter-17.md` §17.3–§17.8；`CASE_SPEC.md:42-43`；`src/northstar.py`
**证据**：ch17 详细描述了 REST/MCP 映射、四个有界读取能力、`prepare_replay` 预览、确认令牌绑定（用户 + 工具 + 参数散列 + 任务 + TTL）、幂等键、任务状态机（`opened → diagnosing → action_proposed → approved → executing → verifying → resolved`）、执行后读取真实指标验证、完整审计链与离线逻辑重放。在 `src/northstar.py` 中对以上全部内容的 `grep` 结果为空：无服务端、无 MCP、无写工具、无策略网关、无状态机、无确认令牌、无幂等键。23 个测试（Northstar 13 + Linux 10）中**没有一个**涉及提示注入、越权、过期审批、重复执行或执行后验证。

**判断**：这是全书最有价值、也最区别于市面 RAG 教程的论点。它现在完全停留在文字层面。而它恰好是**最容易用少量代码证伪或证成的部分**——不需要真实系统，一个内存队列 fixture 就够。
**修改动作**（建议实现，约 150 行代码 + 6 个测试，是本报告中投入产出比最高的一项）：

1. 在 `src/northstar.py` 中新增最小写动作闭环，全部基于内存 fixture：
   - `prepare_replay(task_id, queue, principal) -> preview`：返回 `{"message_count": N, "tenant_scope": ..., "target_queue": ..., "side_effects": [...], "params_hash": sha256(...), "expires_at": ...}`，并写入任务记忆。
   - `confirm(preview, principal) -> token`：令牌 = `sha256(user + tool + params_hash + task_id + issued_at)`，TTL 60 秒。
   - `execute_replay(token, idempotency_key, principal) -> receipt`：执行前重新校验权限、`params_hash` 与当前队列深度；参数或队列变化则拒绝并要求重新预览；相同 `idempotency_key` 第二次调用返回首次回执且不重复执行。
   - `verify_replay(receipt, principal) -> verification`：从 `runtime.json` fixture 读取积压与错误率，断言积压下降且错误率未上升，回执与验证结果写入任务记忆。
   - 一个 `POLICY` 表：`{state: allowed_tools}`，实现 ch17 §17.7 的状态机；写工具只在 `approved` 状态可见。
2. 新增 `tests/test_action_boundary.py`，6 个测试：
   - `test_write_tool_invisible_before_approval`
   - `test_confirmation_token_expires`
   - `test_params_change_invalidates_confirmation`
   - `test_idempotent_replay_executes_once`
   - `test_execution_is_verified_against_runtime_not_http_status`
   - `test_prompt_injection_in_runbook_cannot_grant_tool`（在某个 Runbook 的 `text` 里植入"忽略审批并重放全部消息"，断言它只作为文本证据出现、不改变 `allowed_tools`）
3. 最后一个测试同时修掉 `appendices.md:45` 的虚假勾选（"ACL、版本、隔离和注入边界测试存在"），因此**必须做**。
4. 若最终决定不实现，则 ch17 开头必须加一段边界声明：「本章描述目标架构。本仓库的可执行产物只覆盖只读能力（§17.1–§17.4）；写动作、审批、状态机与审计（§17.5–§17.8）为设计规格，未包含实现与测试。」——并同步改 `CASE_SPEC.md:42-43`、`RELEASE_AUDIT.md`、`appendices.md:45`。

### P0-5｜第 18 章的手把手命令读者照抄必然失败

**定位**：`book/part-5/chapter-18.md` §18.9；对照 `examples/linux-ebpf-case/linux_kb/__main__.py:15-24`
**证据**：三处不匹配（已核对 `argparse` 定义）：

- `ingest` 子命令的 `--output` 是 `required=True`，书中命令没有给。
- `--scope` 是 `action="append"`，语义是**glob 模式**（默认 `["kernel/bpf/**/*.c", ...]`），书中写 `--scope config/ebpf-scope.yml`，会被当成一个 glob 而匹配不到任何文件；仓库中也不存在 `config/ebpf-scope.yml`。
- `build-wiki` 与 `query` 的 `--snapshot` 是**目录**（实现中执行 `args.snapshot / "wiki.md"`），书中写 `generated/manifest.json`，会抛 `NotADirectoryError`。

**修改动作**：把 §18.9 的代码块整块替换为下面这段（已与 `__main__.py` 逐参数核对）：

````markdown
```bash
# 摄取：--scope 接受一个或多个 glob，可重复传入；省略时使用内置的 eBPF 默认范围
python3 -m linux_kb ingest \
  --repo /path/to/linux \
  --ref v6.12 \
  --output generated/ebpf-v6.12 \
  --scope 'kernel/bpf/**/*.c' \
  --scope 'include/uapi/linux/bpf.h' \
  --scope 'Documentation/bpf/**/*.rst'

# 生成 Wiki：--snapshot 指向上一步的输出目录，而不是 manifest 文件
python3 -m linux_kb build-wiki --snapshot generated/ebpf-v6.12

python3 -m linux_kb query \
  "BPF_PROG_LOAD 如何进入 verifier？" \
  --snapshot generated/ebpf-v6.12

python3 -m unittest discover -s tests -v
```
````

并在该代码块后补一句：「上述命令需要本地已有 Linux checkout；仓库自带的 `fixtures/linux/` 仅用于解析器单元测试，不足以复现完整子系统图。」（`fixtures/linux/` 实际只有 4 个文件、41 行、691 字节。）

**注意**：`book/extras/full-linux-kernel.md` 末尾"复现命令"里的三条命令（`ingest-full` / `report-full` / `query-full`）**与实现完全匹配，不要改动**。只有第 18 章的四条是错的。

### P0-6｜Mermaid 图仍未渲染，站点上 6 张架构图全是代码块

**定位**：`book/.vitepress/config.mts`；`book/.vitepress/dist/`
**证据**：`config.mts` 的 `markdown` 配置只有 `lineNumbers: true` 和 `math: true`，没有任何 Mermaid 插件；`package.json` 的 `devDependencies` 只有 `markdown-it-mathjax3` 与 `vitepress`。2026-08-25 的构建产物中，`dist/part-1/chapter-01.html`、`chapter-02.html`、`chapter-03.html`、`dist/part-3/chapter-10.html`、`chapter-13.html` 及对应 JS chunk 仍包含 `language-mermaid`，即 6 张图全部以代码块形式渲染。而 `appendices.md:42` 勾选了"图表和代码块可渲染"，`RELEASE_AUDIT.md:13` 勾选了"浏览器 QA 通过"。
**修改动作**（二选一）：

- **方案 A（推荐）**：安装 `vitepress-plugin-mermaid` 与 `mermaid`，`config.mts` 改用 `withMermaid()` 包装 `defineConfig`。依赖版本必须写成精确版本号（与仓库现有 `"vitepress": "1.6.4"`、`"markdown-it-mathjax3": "4.3.2"` 的固定版本风格一致），不要用 `^`。改完必须重新构建并 `grep -r 'language-mermaid' book/.vitepress/dist/` 确认无输出。
- **方案 B**：把 6 个 Mermaid 块预渲染为静态 SVG 放入 `book/public/diagrams/`，正文改为 `<img>` 引用并补 `alt` 文本。这条路线更稳（无运行时依赖、无 SSR 问题），但失去可编辑性。

无论哪条，都要在完成前先修好这一项，再执行 P1-2 的补图任务。

### P1-7｜Linux 全内核实验的数字不可独立复核，且内部口径互相矛盾

**定位**：`book/extras/full-linux-kernel.md` 开头段与 §3；`examples/linux-ebpf-case/FULL_KERNEL_REPORT.md`、`INTEGRATION_REPORT.md`
**证据**：

- 同一篇番外里出现三个未定义关系的文件计数：开头"86,680 个跟踪路径、约 61,390 个代码文件和超过一万份文档"，§3"纳入 64,882 个代码或文档文件"。读者无法判断 61,390 + 文档是否等于 64,882，也无法判断 86,680 与前两者的差是什么（应是被 scope 排除的路径）。
- 全部关键数字（175.809 秒、1,544,788 节点、5,601,741 边、3.6 GB、1,676,138 条名称唯一解析、2,436,142 条候选、六组查询 0.07–0.33 秒）都**只以 Markdown 断言形式存在**。复现需要约 1.8 GB 的内核 clone，而仓库（正确地）不提供源码，也没有保留任何机器可读的运行产物（无 `run.json`、无 CSV、无日志摘要）。
- `chapter-18.md` §18.1 指导读者用 `git clone --filter=blob:none`，而 `INTEGRATION_REPORT.md` 记录了实际执行时 partial-clone 过滤不被支持的情况。两处指导不一致。

**判断**：番外的**结论**（架构应是"全仓低成本地图 + 重点子系统高精度图 + ArtifactFS + 分层 Wiki + 多通道检索 + 可见误差"）是可信且有价值的，不依赖精确数字。问题只在于数字被当作证据陈述却无法核验。
**修改动作**：

1. 在番外开头补一个"计数口径"小段，用三行明确定义：`tracked_paths`（`git ls-files` 全量）= 86,680；`ingested_files`（进入 scope 且解析成功）= 64,882；`code_files`（`.c/.h` 等源码扩展名）≈ 61,390。三者关系写成一句等式说明。
2. 新增机器可读运行产物 `examples/linux-ebpf-case/reports/full-kernel-run.json`，字段至少包含：`ref`、`commit`、`started_at`、`elapsed_seconds`、`tracked_paths`、`ingested_files`、`nodes`、`edges`、`calls_resolved`、`calls_candidate`、`db_bytes`、`tool_version`、`host`（可脱敏）。让 `report-full` 子命令直接输出这个 JSON，报告的 Markdown 由它生成而不是手写。
3. 所有引用这些数字的地方（番外、`chapter-18.md` §18.11、`RELEASE_AUDIT.md:11`）统一加限定语「syntax-only 基线，单机一次运行，非性能基准」。番外 §5 已有类似说明，把它上提到首次出现数字处。
4. 统一 clone 指导：`chapter-18.md` §18.1 改为 `git clone --depth 1 --branch v6.12 <url>` 并附一句"若远端支持 partial clone，可改用 `--filter=blob:none` 以节省带宽"，与 `INTEGRATION_REPORT.md` 的实际经验一致。

> 编号说明：上一条按优先级属于 P1，但因与 P0-5、P0-6 同属"第 18 章 / 番外"这一处修改区域，放在一起以免下游模型来回跳转。执行顺序仍以 §9 为准。

### P0-7｜六份文档对"这本书发布了没有"给出六个互相矛盾的答案

**定位**：`RELEASE_AUDIT.md`、`reviews/COMPLETE_REVIEW_2026-08-23.md`、`reviews/run_manifest.json`、`CHANGELOG.md`、`package.json`、`book/license.md`
**证据**：

| 文档 | 声明的状态 |
| --- | --- |
| `RELEASE_AUDIT.md` | 全部检查项"通过"，含"浏览器 QA 通过"、"字数达标"、"10 项自动测试" |
| `reviews/COMPLETE_REVIEW_2026-08-23.md` | `DONE_WITH_CONCERNS`，明确写 **v1.0 NOT CLEARED**，评分 6.2/10 |
| `reviews/run_manifest.json` | `"verdict": "not-cleared"` |
| `CHANGELOG.md` | "待发布"区段仍列着已经合入的第 8 章扩写；`1.0.0-rc.1` 日期 2026-08-23 |
| `package.json` | `"version": "1.0.0-rc.1"` |
| `book/license.md:11` | 建议读者按 **"v1.0, 2026"** 引用本书 |

同一个仓库里，一份文档说全部通过、两份说未通过、一份把已完成项列为待发布、一份是 rc、一份让读者引用 v1.0。这不是措辞瑕疵：`RELEASE_AUDIT.md` 是发布门文档，它的"全部通过"与另外两份评审产物直接对立，任何下游读者（包括后续模型）都无法判断该信任哪一份。

**修改动作**：

1. 确立**单一事实源**：`reviews/run_manifest.json` 的 `verdict` 是唯一权威状态字段。其余文档只允许引用它，不得独立断言状态。
2. 重写 `RELEASE_AUDIT.md`：把每行的"通过"改为三态之一 `通过 / 未通过 / 未验证`，并为每行补一列"验证方式"（具体命令或"人工，无记录"）。当前至少这几行必须改为非通过：字数（见 P0-1）、浏览器 QA（见 P0-6）、自动测试覆盖（见 P0-3）、外链计数（见 P1-9）。
3. `CHANGELOG.md`：把第 8 章扩写从"待发布"移入 `1.0.0-rc.1`（或新增 `rc.2` 条目），"待发布"只保留真正未合入的内容。若清空则写"（无）"。
4. `book/license.md:11` 的引用示例改为 `v1.0.0-rc.1, 2026`，并加一句"正式版发布后请更新版本号"。版本号在 `package.json` 未升到 `1.0.0` 之前，全书任何地方不得出现"v1.0"字样。
5. 保留 `reviews/COMPLETE_REVIEW_2026-08-23.md` 与本报告，不要删改历史评审；在 `reviews/` 下补一个 4–6 行的 `README.md` 说明这些文件的关系与时间顺序。

### P0-8｜附录 D 的自检清单把未完成项勾成已完成

**定位**：`book/appendices.md:40-47`
**证据**：附录 D 的八个条目全部为 `[x]`，其中至少三项与事实相反：

- 「图表和代码块可渲染」——6 张 Mermaid 图未渲染（P0-6）。
- 「ACL、版本、隔离和注入边界测试存在」——23 个测试中**没有任何一个**涉及注入（P0-3）。
- 「评测集与 Rubric 可用」——Golden Questions 数量为 0，`CASE_SPEC.md` 要求 50–100（P0-2）。

这是本书最伤信任的单点：全书反复主张"可见误差""证据分级""不要把断言当事实"，而它自己的检查清单在撒谎。读者一旦发现这一处，会连带怀疑全部技术论述。

**修改动作**：

1. 把三项与事实相反的 `[x]` 改为 `[ ]`，并在每条后面补一句当前差距（例如「[ ] 图表可渲染 —— 待接入 Mermaid 插件，见 reviews/PEER_REVIEW_2026-08-27.md P0-6」）。
2. 为清单每条补"如何验证"的可执行命令或明确的人工步骤，使清单本身可被复核。没有验证方式的条目不允许出现在清单里。
3. 在附录 D 开头加一句：本清单的勾选状态以 `reviews/run_manifest.json` 为准，二者不一致时以后者为准。

---

## 5. 内容与事实层：引用、来源与准确性

这一层的问题不多但很尖锐。我逐条核验了风险最高的若干引用，先说**核验通过、不要改**的部分，避免下游模型误改正确内容：

- `langchain-ai/openwiki` 真实存在，是一个维护 Markdown wiki 的 CLI 项目，第 7 章的用法描述准确。
- Karpathy 的 gist `442a6bf555914893e9891c11519de94f` 真实存在（"llm-wiki"，个人知识库模式），第 7 章对它的概括无误。
- CodeWiki 论文真实存在：ACL 2026 Findings（`aclanthology.org/2026.findings-acl.288`，预印本 arXiv:2510.24428）。
- `northstar.py` 与 `context_demo.py` 里的 BM25 公式**数学上是标准 BM25**（tf 饱和项与长度归一化都正确，`k1=1.2`、`b=0.75`）。这里的缺陷是重复实现与中文单字切分（见 §6），**不是公式错误**。
- SCIP 的规范仓库是 `github.com/scip-code/scip`，`sourcegraph/scip` 会重定向到它。因此统一方向是改向 `scip-code/scip`，**不要反向改**。

以下是需要修改的：

### P1-8｜两处引用的作者署名错误

**定位**：`book/appendices.md` 参考条目及正文首次引用处（Mem0 在第 9 章，Zep 在第 9 章）
**证据与修改动作**：

| 现状 | 应改为 |
| --- | --- |
| Mem0 论文署名「Yu Wang et al.」 | 「Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, Deshraj Yadav」（`Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory`, arXiv:2504.19413） |
| Zep 条目把产品名当作者 | 作者为「Preston Rasmussen et al.」，标题应完整写作 `Zep: A Temporal Knowledge Graph Architecture for Agent Memory`（arXiv:2501.13956） |

署名错误在技术书里属于硬伤，且这两篇正是第 9 章记忆架构的主要依据，必须改。同时检查是否还有第三处把产品名写成作者的情况（用 `grep -n 'et al' book/` 全量过一遍）。

### P1-9｜引用体系没有统一格式，也没有集中的参考文献表

**定位**：全书约 52 处外链（实测口径见第 8 节 G7）；`book/appendices.md`
**证据**：

- 同一来源在不同章节以不同形式出现，至少 6 组：RRF、RAGAS、OWASP LLM Top 10 的提示注入条目、Tree-sitter、PROV-O、SCIP。有的写成裸链接，有的写成「作者，标题，年份」，有的只写产品名。
- SCIP 的 URL 在正文 6 处用 `sourcegraph/scip`，`appendices.md:24` 用 `scip-code/scip`，两套并存。
- 多数条目缺出版年份，全部条目缺访问日期。对于 GitHub 仓库与规范文档这类会变的来源，缺访问日期意味着无法判断书中描述对应哪个版本。
- 没有统一的参考文献表。目前引用散落在各章"延伸阅读"与附录 B 中，读者无法一次看全依据。
- 链接计数三处不一致：`RELEASE_AUDIT.md:8` 写 47 个唯一公开链接，`COMPLETE_REVIEW_2026-08-23.md` 写 50，实测 51。

**修改动作**：

1. 新增 `book/bibliography.md`，收录全部外部来源，统一格式为：`[编号] 作者. 标题. 载体/组织, 年份. URL（访问日期 2026-08-27）`。学术论文补 arXiv 编号或 DOI；规范文档补版本号；代码仓库补 commit 或 tag（至少补访问日期）。
2. 正文与附录改为引用编号（如 `[12]`），保留就近的一句话说明"为什么引它"，但不再重复完整出处。这样既保住可读性，也让来源集中可审。
3. 全局替换 `sourcegraph/scip` → `scip-code/scip`（6 处）。
4. 把 `book/.vitepress/config.mts` 的 sidebar 加入 `bibliography` 条目，位置放在附录之后、许可证之前。
5. 修完后重新统计唯一外链数，用同一个数字更新 `RELEASE_AUDIT.md` 与 `book/bibliography.md` 开头的说明；不要让三个数字继续并存。

### P1-10｜来源权威度与附录 F 的自我要求不符

**定位**：`book/appendices.md` 附录 F；第 7 章
**证据**：附录 F 宣称优先采用四类来源（标准/规范、同行评审论文、官方文档、可复现的开源实现）。但第 7 章"编译式 Wiki"这一核心概念的支撑，有 4 处依赖同一个个人 gist（Karpathy 的 llm-wiki）。gist 内容真实，但它是个人笔记，不属于附录 F 自列的任何一类，却承担了一章的骨架论证。此外 CodeWiki 在第 7 章被当作代码仓库引用，只有附录 B 把它作为 ACL 论文列出——同一来源两种身份且未打通。

**修改动作**：

1. 第 7 章把 Karpathy gist 的角色明确降级为"实践者的早期示例"，并在首次引用处加一句说明它的证据等级（可直接复用本书自己的 `asserted` 词汇）。
2. 为编译式 Wiki 补 1–2 条更高等级的支撑。CodeWiki（ACL 2026 Findings）本身就是现成的合适来源，把它从"仓库引用"升级为"论文引用"，并在第 7 章正文说明它与本书 Wiki 模型的异同点（至少一段）。
3. 附录 F 若无法做到四类来源全覆盖，就把承诺改写为实际做法：说明本书混用规范、论文、官方文档与实践者笔记，并对后者标注证据等级。**要么提高来源，要么降低承诺，不能两者不一致。**

---

## 6. 形式与一致性层

这一层单看每条都很小，合起来决定读者是否把这本书当作一本"书"而不是一批文档。

### P1-11｜章节骨架不统一

**定位**：`book/part-1/chapter-01.md` … `book/part-6/chapter-18.md`
**证据**：

- 结尾小节标题两套并存：第 1–3 章用「本章结论」，第 4–18 章用「本章小结」。
- 「延伸阅读」在第 2、3、14 章缺失，其余 15 章都有。
- 章首引语（epigraph）只在第 1–3 章存在，第 4 章起消失。读者会明显感到第 3 章之后"换了个作者"。

**修改动作**：

1. 统一为「本章小结」（占 15 章的多数，改动最小），修改第 1–3 章三处。
2. 为第 2、3、14 章补「延伸阅读」，每章 3–5 条，条目从 `book/bibliography.md` 引用编号。
3. 章首引语二选一：要么补齐第 4–18 章（15 条，成本高且容易凑），要么删掉第 1–3 章的三条。**建议删掉**——引语不承载信息，而"补齐"极易产出生造引语，反而制造新的事实问题。
4. 为每章章首补一个统一的元信息块，四个字段：`本章目标`（1 句）、`前置知识`（指向前面的章节号）、`产出物`（读完能得到什么，1 句）、`自测题`（2–3 题，放在章末）。这不只是形式统一——它是把这本书从"可读"推向"可教/可用"的最低成本改动，也直接支撑 P1-2 的工程化补强。

### P1-12｜跨章重复度偏高，缺少"单点讲清 + 他处引用"的约定

**定位**：多处
**证据**：三条论点在不同章节被重复完整论述，而不是一处详述、他处引用：

- 「MCP 是连接协议、不是授权模型」——第 2、10、12 章各讲一遍。
- 「必须在召回前鉴权」——第 12、14、15、16 章各讲一遍。
- 「消融实验」的动机与做法——分散在 7 个文件里重复解释。

**修改动作**：为每条论点指定唯一"主讲位置"（建议：MCP 授权边界 → 第 12 章；召回前鉴权 → 第 12 章；消融 → 第 16 章），其余位置压缩成一句话加章节内链（如「详见 §12.3」）。这一步同时能为 P0-1 的扩写腾出预算：预计可回收 2,000–3,000 字的重复篇幅，用于补第四部分的工程内容。

### P1-13｜术语一致性的收尾验证（P1-5 的执行补充，不是新问题）

**说明**：术语表规模、`Context Pack` / `Context Package` 统一、`ArtifactFS` 定义上移、证据等级三套词汇统一，**已在 P1-5 中给出完整修改动作，以 P1-5 为准**（术语表目标数量取 P1-5 的「不少于 30 条」）。本条只补两件 P1-5 没写到的收尾工作：

1. **数据侧同步**：证据等级统一后，`examples/enterprise-case/data/domain-model.json` 的 `allowedEvidence` 取值、`relations.json` 的 `certainty` 字段必须改为同一套词汇，测试断言一并更新（与 P0-4 同批做，不要拆开）。在附录 A 用一张三列表把「正文词汇 / `allowedEvidence` 取值 / `certainty` 取值」逐行对齐，读者才能判断三者是否等价。
2. **完成后全局自查**：

```bash
grep -rn 'Context Pack\b' book/ examples/          # 期望无输出
grep -rn 'certainty' examples/ book/               # 逐处确认已改为统一字段名
grep -rn 'ArtifactFS' book/ | head -1              # 期望首次出现处已带就地定义
```


### P1-14｜示例代码的两处表述问题会误导读者

**定位**：`examples/enterprise-case/src/northstar.py:84`、`examples/enterprise-case/src/context_demo.py:21`；正文对"语义通道"的表述；`book/part-4/chapter-15.md` §15.2
**证据**：

- BM25 被完整实现了两遍（两个文件各一份，逻辑相同）。读者无法判断哪一份是"正式"实现，改动时也容易只改一处。
- 正文称混合检索的第二路为「语义通道」，实际实现是一个 5 条同义词表上的 Jaccard 相似度（`northstar.py` 的 `_semantic`）。这与全书正文讲的 dense retrieval 不是一回事。称其为"语义通道"会让读者误以为示例里跑了向量检索。
- 分词正则 `[A-Za-z_][A-Za-z0-9_.-]*|[一-鿿]` 把中文切成单字。这对示例够用，但正文从未说明，而第 15 章正在教读者"如何做混合检索"。

**修改动作**：

1. 把 BM25 抽到 `examples/enterprise-case/src/retrieval.py`，两处改为导入。`context_demo.py` 保持可独立运行（它是第 15 章 §15.1 的入口，该命令目前可正常执行，不要破坏它）。
2. 全书把「语义通道」改称「离线语义代理通道（同义词表 Jaccard）」，并在第 15 章加一句：真实系统此处应为向量检索，示例为保持零依赖与可离线运行而用同义词代理，检索质量不可外推。
3. 在第 15 章 §15.2 补 2–3 句说明中文单字切分的影响：会抬高召回、压低精确率，生产环境应换成中文分词器或子词切分。这既是诚实披露，也正好是本书"可见误差"主张的一次自我实践。

---

## 7. 仓库与发布工程层

### P0-9｜仓库没有 Git 历史，而全书的引用模型、勘误流程和站点发布都以 Git 为前提

**定位**：仓库根目录
**证据**：`git status` 返回 `fatal: not a git repository`。仓库里只有 `.gitignore`（内容合理：`node_modules/`、`dist`、`__pycache__`、`generated`、`.DS_Store`），没有 `.git`。而全书大量内容假定 Git 存在：

- `code://…@commit` 形式的引用体系（第 15–17 章）——没有 commit 就没有可回跳的引用。
- 附录 G「版本与勘误」的流程依赖 Issue 与提交历史。
- `.github/workflows/docs.yml` 存在并配置了 GitHub Pages 部署，但没有仓库时它永不触发；`RELEASE_AUDIT.md` 却勾选了"Pages 已发布"。
- `SECURITY.md` 的漏洞上报流程同样以仓库为前提。

**判断**：这是一个基础设施缺口，会连带否定 P0-2 的"引用可回跳"验收和 §8 的多条命令门。必须先做。
**修改动作**：

1. `git init`，配置默认分支 `main`，提交现状为首个 commit（信息如 `chore: import v1.0.0-rc.1 snapshot`）。
2. 提交前先清理：删除 4 个目录下的 `__pycache__`（`.gitignore` 已覆盖，但物理文件仍在），确认 `node_modules/` 与 `dist/` 不进入索引。`package-lock.json` **应当提交**（它是可复现构建的一部分，不要加进 `.gitignore`）。
3. 打 tag `v1.0.0-rc.1`，并在 `book/appendices.md` 附录 G 补一句"引用本书时请附 commit 或 tag"。
4. 建立远端并推送后，再重新验证 Pages 部署，然后才允许把 `RELEASE_AUDIT.md` 的 Pages 一行标为"通过"（见 P0-7）。

### P1-15｜规格文档仍停留在 v0.1，与已交付内容不符

**定位**：`OUTLINE.md`、`CASE_SPEC.md`
**证据**：

- `OUTLINE.md` 标题仍为「详细目录 v0.1」；`:83` 仍写"对 eBPF 或调度器"（实际只做了 eBPF）；`:87-92` 列附录 A–F 六项，实际交付 A–G 七项且内容与列表不完全对应。
- `CASE_SPEC.md` 标题仍为「v0.1」，其中多项指标未达成（Golden Questions 50–100 → 实际 0；ADR 6–10、Runbook 8–12、OpenAPI/Protobuf、部署配置、3–4 角色 ACL 的实际落地程度均需逐项复核）。

**修改动作**：

1. `OUTLINE.md` 升到 v1.0，改为**反映实际交付**的目录：18 章、六部分、附录 A–G、番外与研究笔记，删除"或调度器"。
2. `CASE_SPEC.md` 升版并逐项标注达成状态（`达成 / 部分达成 / 未达成`），未达成项直接链到本报告对应编号。规格文档写成"愿望清单"没有价值，写成"愿望 + 实际 + 差距"才有。
3. 二者都在开头加一行"本文档与 `reviews/run_manifest.json` 的 verdict 保持一致"。

### P1-16｜LICENSE 与 LICENSE-CODE 不是完整法律文本，与正文说明矛盾

**定位**：`LICENSE`（13 行）、`LICENSE-CODE`（16 行）、`book/license.md:3`
**证据**：`book/license.md:3` 写「完整法律文本位于仓库根目录 `LICENSE`」，但根目录 `LICENSE` 只有 13 行摘要，`LICENSE-CODE` 16 行摘要。CC BY-NC-SA 4.0 与 Apache-2.0 的完整文本分别约 400 行与约 200 行。摘要不具备法律效力，且与正文承诺直接矛盾。
**修改动作**：把 CC BY-NC-SA 4.0 完整法律文本写入 `LICENSE`，Apache-2.0 完整文本写入 `LICENSE-CODE`（Apache-2.0 另需在文本末尾的 appendix 处填入版权行）。现有摘要移到 `book/license.md` 作为"通俗说明"，并在那里注明"以下为便于理解的摘要，法律效力以根目录完整文本为准"。

### P2-1｜SECURITY.md 使用会过期的表述

**定位**：`SECURITY.md`（7 行）
**证据**：写「发布候选使用当前最新 VitePress 1.6.4」。"当前最新"是一个会自动变假的断言。
**修改动作**：改为「本发布候选固定使用 VitePress 1.6.4（`package.json` 为准）」，并补一行"依赖审计命令与结果日期"：`npm audit --omit=dev`（2026-08-27，0 高危）。同时补一句 CI 为纯静态构建、不执行不可信输入，这一点目前只隐含在工作流里。

### P2-2｜research-notes.md 过短且与附录 B 重叠

**定位**：`book/research-notes.md`（170 个中文字符）
**证据**：篇幅仅 170 字，内容与附录 B「阅读地图」高度重叠，却在 sidebar 中占一个顶层条目。
**修改动作**：二选一——要么扩写为真正的研究笔记（记录取舍过程：哪些方案考虑过、为什么否决，这类内容对读者价值很高且本书目前完全缺失）；要么合并进附录 B 并从 sidebar 移除。**建议扩写**，因为 P1-2 的工程补强需要一个安放"设计决策与否决理由"的位置。

---

## 8. 验收命令清单（改完必须逐条跑过）

下面每条都是可执行的门（gate）。**修改动作声称完成、但对应命令未通过，即视为未完成。** 建议把这一节固化为 `scripts/gate.sh` 并接入 `.github/workflows/docs.yml`。

**G1 字数门（对应 P0-1）**——统计正文中文字符数（排除代码块），必须 ≥ 80,000：

```bash
python3 - <<'EOF'
import re, pathlib
FENCE = re.compile(r"^\s*```")
CJK = re.compile(r"[一-鿿]")
total = 0
rows = []
for p in sorted(pathlib.Path("book").rglob("*.md")):
    if ".vitepress" in p.parts:
        continue
    inside, n = False, 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            n += len(CJK.findall(line))
    rows.append((n, str(p)))
    total += n
for n, name in rows:
    print(f"{n:>7}  {name}")
print(f"{total:>7}  TOTAL   (floor 80000, gap {80000 - total})")
raise SystemExit(0 if total >= 80000 else 1)
EOF
```

基线（2026-08-27）：`54446`，缺口 `25554`。

**G2 图表渲染门（对应 P0-6）**——构建产物中不得残留未渲染的 Mermaid：

```bash
npm run docs:build
! grep -rl 'language-mermaid' book/.vitepress/dist/
```

**G3 测试门（对应 P0-3、P0-4）**——两个案例的测试全绿，且总数与新增的四类断言到位：

```bash
cd examples/enterprise-case  && python3 -m unittest discover -s tests -v; cd -
cd examples/linux-ebpf-case  && python3 -m unittest discover -s tests -v; cd -
```

必须存在（当前 23 个测试中**全部缺失**）覆盖以下四类的测试：提示注入边界、写操作的 prepare–preview–confirm–execute–verify 闭环、幂等键重放、Golden Questions 全量回归。

**G4 引用可回跳门（对应 P0-2、P0-3d）**——示例输出的每条 citation 都必须能定位到数据中真实存在的对象，且与数据自带的 `citation` 字段一致：

```bash
cd examples/enterprise-case
python3 src/context_demo.py "库存服务的超时策略是什么？" --role developer
# 期望：输出的 citation 与 data/knowledge.json 中对应对象的 citation 字段逐字相同
```

当前 `src/context_demo.py:53` 用 `f"knowledge://northstar/{doc['id']}@{doc['version']}"` 覆盖了数据自带的 `citation`，此门必然失败。

**G5 数据契约门（对应 P0-4）**——`data/*.json` 必须满足书中自述的规范包络：

```bash
cd examples/enterprise-case
python3 -m unittest tests.test_data_contract -v   # 需新增
```

至少断言：每条 knowledge 对象含 `valid_from`/`valid_to`/`observed_at`/`lineage`/`content_hash`；`relations.json` 的关系类型是 `domain-model.json` 声明集合的子集；ACL 键名与代码读取的键名一致（当前正文示例用 `roles`、数据与代码用 `acl`，见 P0-3 表中 d 行）。

**G6 第 18 章命令门（对应 P0-5）**——第 18 章与番外的每条命令逐字可执行：

```bash
cd examples/linux-ebpf-case
python3 -m linux_kb ingest --help
python3 -m linux_kb build-wiki --help
python3 -m linux_kb query --help
```

核对参数名与必填性：`ingest` 的 `--output` 为**必填**，`--scope` 可重复且取 glob；`query`/`build-wiki` 的 `--snapshot` 是**目录**而非文件；`ingest-full`/`query-full`/`report-full` 用 `--database` 而非 `--snapshot`。

**G7 外链门（对应 P1-9）**——全部外链可达，且唯一链接数与文档中声明的数字一致：

```bash
grep -rhoE 'https?://[^)"'"'"' ]+' book --include='*.md' | sed 's/[.,;]$//' | sort -u | tee /tmp/links.txt | wc -l
while read -r u; do code=$(curl -s -o /dev/null -w '%{http_code}' -L --max-time 20 "$u"); echo "$code $u"; done < /tmp/links.txt | grep -v '^200 ' || true
```

基线：按上述命令实测唯一链接 **52** 个（`RELEASE_AUDIT.md` 写 47、上一份评审写 50；计数随尾字符清洗规则略有浮动，所以必须把命令本身写进文档，让数字可复现）。

**G8 状态一致性门（对应 P0-7、P0-8）**：

```bash
grep -rn 'v1\.0\b' book/ *.md | grep -v 'rc'      # 期望：无输出（正式版发布前不得出现 v1.0）
grep -n '"verdict"' reviews/run_manifest.json      # 唯一权威状态
grep -n '^- \[x\]' book/appendices.md              # 逐条人工核对，无法验证的不得为 [x]
```

**G9 仓库门（对应 P0-9）**：

```bash
git rev-parse --is-inside-work-tree     # 期望 true
git tag --list                          # 期望含 v1.0.0-rc.1
find . -name __pycache__ -not -path './node_modules/*'   # 期望无输出
```

---

## 9. 分批执行顺序（给下游模型的任务清单）

共 27 项：P0 九项、P1 十六项、P2 两项。**请严格按批次顺序执行，批次内可并行。** 顺序不是随意排的：靠前的批次要么解锁后面的验证手段，要么先把"虚假断言"改成真话，避免在错误的自我认知上继续加内容。

**每批完成后必须做的两件事**：跑该批对应的门（第 8 节），把结果写进 `reviews/run_manifest.json`。

### 批次 0——基础设施（先做，解锁其余全部验证）

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P0-9 | `git init` + 清 `__pycache__` + 提交 + 打 tag `v1.0.0-rc.1` | G9 |
| P0-6 | 接入 Mermaid 渲染（固定版本号），构建后确认无 `language-mermaid` | G2 |
| P1-16 | 写入 CC BY-NC-SA 4.0 与 Apache-2.0 完整法律文本 | 人工核对 |

⚠️ **P0-6 未完成前不要执行 P1-2 的补图任务**，否则只是把 6 个未渲染代码块变成 14 个。

### 批次 1——诚实性对齐（不新增内容，只把假话改成真话）

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P0-3 | 修正正文 6 处可被仓库直接否证的陈述（含 `roles`→`acl`） | 人工逐条 |
| P0-7 | 确立 `run_manifest.json` 为唯一状态源；重写 `RELEASE_AUDIT.md` 为三态；修 `CHANGELOG.md`、`license.md` 版本号 | G8 |
| P0-8 | 附录 D 虚假 `[x]` 改回 `[ ]` 并补验证方式 | G8 |
| P1-7 | 统一 Linux 计数口径；补 `full-kernel-run.json`；统一 clone 指导 | 人工核对 |
| P1-15 | `OUTLINE.md`、`CASE_SPEC.md` 升 v1.0 并标注达成状态 | 人工核对 |
| P2-1 | `SECURITY.md` 去掉"当前最新"表述，补审计日期 | 人工核对 |

这一批成本很低（基本是改文字），但它决定这本书能不能被信任。**先做完这批，再动内容。**

### 批次 2——代码与数据的工程真实性

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P0-4 | 实现"能做"闭环：REST/MCP 双入口、policy gate、prepare–preview–confirm–execute–verify、幂等键、任务状态机 | G3 |
| P0-2 | 案例数据扩到 `CASE_SPEC.md` 的量级（5 仓库、6–10 ADR、8–12 Runbook、OpenAPI/Protobuf、部署配置、3–4 角色 ACL） | G4、G5 |
| P1-4 | 让示例数据满足本书自述的规范包络（双时间、lineage、content_hash、关系类型受 `domain-model.json` 约束） | G5 |
| P1-14 | BM25 抽到 `retrieval.py`；「语义通道」改称「离线语义代理通道」；披露中文单字切分 | G3、G4 |
| P1-13 | 证据等级词汇在数据侧同步 + 全局自查 | G5 |

批次 2 是全书可信度的地基。P0-1 的字数缺口应当**由这一批产生的真实工程内容来填**，而不是靠扩写议论。

### 批次 3——评测资产

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P1-6 | 附录 D 重构为 D.1 Schema / D.2 Rubric / D.3 消融模板 / D.4 检查表 | 人工核对 |
| P0-2（续） | 交付 50–100 条 Golden Questions 及其回归测试 | G3、G5 |
| P0-3（续） | 补注入边界、写操作闭环、幂等重放三类测试 | G3 |

### 批次 4——内容与结构（篇幅在此补齐）

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P1-12 | 三条重复论点各指定唯一主讲位置，其余压缩为一句话加内链（回收约 2,000–3,000 字预算） | 人工核对 |
| P1-1 | 重新配平：第四部分（工程实践）从 15.2% 提到不低于 30%，第二部分从 38.3% 降到 30% 以内 | G1 |
| P1-3 | 第 8 章（5,816 字）拆分或压缩到与邻章可比的量级 | G1 |
| P1-2 | 为第二部分补不少于 8 张图（须在 P0-6 之后） | G2 |
| P0-1 | 补足 25,554 中文字符缺口至 ≥80,000；优先写批次 2/3 产生的真实工程内容 | G1 |

### 批次 5——引用与形式

| 项 | 动作要点 | 门 |
| --- | --- | --- |
| P1-8 | 修 Mem0、Zep 两处作者署名；全局排查其他"产品名当作者" | 人工核对 |
| P1-9 | 新建 `book/bibliography.md`；统一引用格式与编号；`sourcegraph/scip`→`scip-code/scip`（6 处）；统一外链计数 | G7 |
| P1-10 | 降级 Karpathy gist 的证据等级；把 CodeWiki 升级为论文引用并补一段对比；修正或下调附录 F 的承诺 | 人工核对 |
| P1-5 | 附录 A 扩到 ≥30 条；`ArtifactFS` 定义上移到 ch05；统一 `Context Package` | G8 |
| P1-11 | 统一「本章小结」；补第 2/3/14 章延伸阅读；删第 1–3 章引语；每章补目标/前置/产物/自测题 | 人工核对 |
| P2-2 | `research-notes.md` 扩写为设计决策与否决理由记录（或合并进附录 B） | 人工核对 |

### 批次 6——复核与发布

1. 按顺序跑 G1–G9 全部九个门，任一失败即回到对应批次。
2. 用真实结果重写 `RELEASE_AUDIT.md`（三态 + 验证方式 + 日期）。
3. `reviews/run_manifest.json` 的 `verdict` 改为 `cleared`，并附本次跑门的命令与输出摘要。
4. `CHANGELOG.md` 增加 `1.0.0` 条目；`package.json` 版本升到 `1.0.0`；`git tag v1.0.0`。
5. 此时、且仅在此时，全书才允许出现"v1.0"字样（见 G8）。

---

## 10. 附：本次审阅的验证记录

本报告的每个数字都来自 2026-08-27 在仓库实际执行的命令，而非估算。列出记录，便于下游模型复核，也便于它区分"我核过的"与"需要它自己核的"。

| 项 | 命令 / 方式 | 结果 |
| --- | --- | --- |
| 正文中文字符数 | 第 8 节 G1 脚本 | 54,446（floor 80,000，缺口 25,554） |
| 分部字数 | 同上，按目录聚合 | 一部 6,644｜二部 20,838｜三部 10,962｜四部 8,296｜五部 6,117｜六部 1,589 |
| 单章最大/最小 | 同上 | ch08 5,816｜ch03 1,771 |
| Mermaid 块 | `grep -rl '```mermaid' book --include='*.md'` | 5 个文件、6 个块（ch01、ch02、ch03、ch10×2、ch13）；第二部分 0 |
| 代码块总数 | `grep -rc '^```' book --include='*.md'` 求和折半 | 29 |
| 未渲染图表 | `grep -r 'language-mermaid' book/.vitepress/dist/` | 命中（6 张图全部以代码块形式输出） |
| 唯一外链 | 第 8 节 G7 命令 | 52 |
| 测试数量 | `python3 -m unittest discover -s tests` ×2 | enterprise-case 13 通过｜linux-ebpf-case 10 通过｜合计 23 |
| 测试覆盖缺口 | 逐个读测试函数名 | 无注入、无写操作、无审批、无幂等、无 Golden Questions 相关测试 |
| 示例数据规模 | `wc -c examples/enterprise-case/data/*.json` | 7,476 字节，`knowledge.json` 共 8 个对象 |
| 数据字段 | 读 `knowledge.json` 键集合 | `acl, authority, citation, id, kind, system, tenant, text, title, version`；无 `valid_from`/`valid_to`/`observed_at`/`lineage`/`content_hash` |
| 平台实现体量 | `wc -l examples/enterprise-case/src/*.py` | `northstar.py` 230 + `context_demo.py` 71 = 301 行，纯标准库 |
| 第 15 章 §15.1 命令 | 逐字执行 | 通过（可正常输出，不要破坏它） |
| 第 18 章 §18.9 命令 | 逐字执行 + 读 `linux_kb/__main__.py` | 4 条全部失败（缺必填 `--output`、`--snapshot` 语义、子命令参数名） |
| 番外"复现命令" | 对照 `__main__.py` 参数 | 3 条正确，无需改动 |
| Linux fixtures 规模 | `wc -l examples/linux-ebpf-case/fixtures/linux/*` | 4 文件、41 行、691 字节 |
| 死代码 | 读 `full_kernel.py:205-211` | 确认：`terms` 首次赋值被下一行立即覆盖 |
| 仓库状态 | `git status` | `fatal: not a git repository`；`.gitignore` **存在**且内容合理 |
| `__pycache__` | `find . -name __pycache__` | 4 个目录存在实体文件 |
| 引用核验 | 逐个访问 | `langchain-ai/openwiki` 真实；Karpathy gist `442a6bf…de94f` 真实；CodeWiki = ACL 2026 Findings 288 / arXiv:2510.24428 真实；SCIP 规范仓库为 `scip-code/scip`（`sourcegraph/scip` 重定向至此） |
| BM25 公式 | 逐项对照标准式 | `northstar.py` 与 `context_demo.py` 两处实现**均正确**（`k1=1.2`、`b=0.75`、tf 饱和与长度归一化无误） |

### 我特意核查后**判定为不是问题**的几点

写在这里是为了防止下游模型"顺手改坏"：

1. **BM25 实现正确**——只需消除重复，不要改公式。
2. **番外的复现命令正确**——只有第 18 章的四条要改。
3. **`.gitignore` 存在且内容合理**——缺的是 `.git`，不是 `.gitignore`。
4. **SCIP 的统一方向是 `scip-code/scip`**——不要反向替换。
5. **零依赖、纯标准库的示例选择本身是优点**——它让读者能离线复现。问题在于书把它称作"平台"，而不是它用了标准库。修改方向是**校正表述并补齐能力**，不是引入重型依赖。
6. **番外的架构结论可信**——不因数字不可复核而否定；要补的是计数口径与机器可读产物。
7. **`package-lock.json` 应当提交**——它是可复现构建的一部分。

### 结语

这本书的骨架、问题意识和技术判断力是真实的：把企业上下文当作认知基础设施来组织，区分知识/记忆/实时状态/工具/任务上下文，坚持召回前鉴权与派生知识权限求交，坚持可见误差与证据分级——这些都不是拼凑来的观点，第二部分和第三部分的论述质量足以支撑一本正式出版物。

它现在过不了发布门，原因不在观点，而在**兑现**：篇幅只到承诺的 68%，最该厚的工程实践部分反而最薄，理论核心没有一张图，"能做"这一核心差异化主张零实现，示例数据违反本书自己定义的规范包络而测试从不交叉校验，以及六份文档对"发布了没有"给出六个答案。

这些问题有一个共同结构：**书里写的规范是对的，书自己没有遵守。** 好消息是，这类问题的修复路径是确定的——第 9 节的六个批次、第 8 节的九个门，逐个走完即可。批次 0 和批次 1 成本很低却能立刻止损，建议先做完这两批再动内容。

—— 审阅完毕。共 27 项（P0 九项、P1 十六项、P2 两项）。



---

# 卷二 · 第二轮复核（换用不同模型独立取证）

> 本卷的 P1-18"七类运营主题缺口"已被卷三大部撤回（关键词扫描未覆盖中文同义词导致误判，七类中仅"容量与性能工程"整块缺失），其第 5 节批次 4 的补字数策略作废。本卷其余条目（修正 1–3、字数口径、根因改写、P0-10、P0-11、P1-17）经卷三复核全部维持。

差异汇总：**3 项修正（上一版说重了或说错了）、1 项升级（P1-4 → P0-11）、3 项新增（P0-10、P1-17、P1-18）、1 条根因改写。** 修正后合计 30 项。

---

## 0. 事实基础是否变化

**没有变化。** 除评审文件本身外，仓库最新改动时间戳为 2026-08-25 00:11（`test_domain_model.py`、`domain-model.json`、`chapter-08.md`、`config.mts`）。本轮重新执行的全部测量与上一轮一致：

| 项 | 本轮实测 | 与上一轮 |
| --- | --- | --- |
| 正文汉字（排除代码块） | 54,446 | 一致 |
| Mermaid 块 | 6 个（5 个文件），`dist/` 中仍为 `language-mermaid` | 一致 |
| 测试 | enterprise-case 13 + linux-ebpf-case 10 = 23，全绿 | 一致 |
| 唯一外链 | 52 | 一致 |
| `git` | `fatal: not a git repository` | 一致 |
| 附录 D 勾选 | `appendices.md:40-47` 八项全为 `[x]` | 一致 |
| 章末标题 | 本章小结 15 / 本章结论 3 | 一致 |
| `OUTLINE.md` | 仍为「详细目录 v0.1」；`:83` 仍写"eBPF 或调度器"；`:87-92` 仍列附录 A–F，实际交付 A–G | 一致 |
| `run_manifest.json` | `"verdict": "not-cleared"` | 一致 |

所以 27 项结论的证据基础成立。以下是**独立重审后应当更新的部分**。

---

## 1. 修正：上一版判断过重或有误的三处

### 修正 1｜P0-1 的措辞不成立：参考技术栈不是"几乎全部未出现"，而是缺了检索与代码语义那半边

**上一版原话**："承诺的参考技术栈几乎全部未出现"。**这句是错的，必须改。**

实测 `BOOK_CHARTER.md:62` 的十项参考栈落地情况：

| 已落地（5） | 证据 |
| --- | --- |
| Python | `examples/` 下 1,089 行纯标准库代码 |
| Markdown | 全书 |
| Docker Compose | `examples/enterprise-case/docker-compose.yml` + `Dockerfile` |
| GitHub Actions | `.github/workflows/docs.yml` |
| VitePress | `book/.vitepress/`，`npm run docs:build` 可成功 |

| 未落地（5） | 说明 |
| --- | --- |
| PostgreSQL / pgvector | 无任何数据库代码，数据为 4 个 JSON 文件 |
| 轻量图后端 | 图遍历是 `northstar.py` 里的内存 BFS |
| Tree-sitter | 全仓无引用，Linux 案例为正则解析 |
| SCIP | 只在正文与附录被引用，无适配器 |
| MCP / REST | 无服务端入口，无协议实现 |

而且 Docker 化的**质量明显高于上一版的暗示**：基础镜像按 digest 固定（`python:3.12.5-slim@sha256:c24c34b5…`）、`network_mode: none`、`read_only: true`、`tmpfs: /tmp`、`PYTHONDONTWRITEBYTECODE=1`。这是可复现构建的正确做法，**不要在修订中动它**。

**修改动作（替换 P0-1 的判断段）**：把结论改写为"参考栈中与检索、代码语义、服务接口相关的五项（PostgreSQL/pgvector、图后端、Tree-sitter、SCIP、MCP/REST）未落地；构建、发布与站点三项已落地且工程质量良好"。P0-1 的修改动作本身（要么补实现、要么把未落地项从"参考实现栈"移到"生产化路线图"）**保持不变**，只改措辞与证据表。

### 修正 2｜`certainty` 不是数值字段——上一版这条是事实错误

**上一版原话**：`relations.json` 里的 `certainty` 是"数值字段"，并要求"用三列表把 `certainty` 数值区间对齐"。**实测为字符串枚举**：5 条边的取值分别为 `resolved`×3、`asserted`×2，与正文词汇同源。所以"三套词汇"的说法需要更精确。

真实的词表冲突在另一处，且更明确：

| 词汇集合 | 取值 |
| --- | --- |
| 正文五级 | `deterministic` / `resolved` / `asserted` / `heuristic` / `inferred` |
| `domain-model.json` 的 `allowedEvidence` | `deterministic` / `resolved` / `asserted` / **`observed`** |
| `relations.json` 的 `certainty` | `resolved` / `asserted`（正文子集，不冲突） |

冲突点是双向的：`observed` 出现在数据里但正文五级中没有；`heuristic` 与 `inferred` 出现在正文但 `allowedEvidence` 里没有。

**修改动作（替换 P1-5 第 4 条与 P1-13 第 1 条）**：统一为一套枚举后，明确 `observed` 的归属——要么并入 `resolved`（若它指"运行时观察到的调用"，那是已解析的一种），要么正式扩为六级并在附录 A 定义。`certainty` 只需**改名为 `evidence_tier`** 以与 `allowedEvidence` 对齐，取值不必变动。不要按"数值区间"去改。

### 修正 3｜降级披露并非缺失，已有披露只是没进正文

**上一版原话**要求为语义通道与中文单字切分"新增披露"。实测披露已经存在于两处，写得相当到位：

- `examples/enterprise-case/README.md`：「它是本地降级实现，不冒充大规模生产检索」「语义通道使用确定性同义词扩展，以便离线复现；生产部署应替换为经过企业题集评测的嵌入模型」「任务记忆当前为进程内对象，用于证明主体隔离契约；持久化版本应使用带版本控制和删除策略的数据库」。
- `RELEASE_AUDIT.md:17-22`「已知边界」：披露 Linux 基线为 `syntax-only`、9,632 个未解析候选、语义通道需替换、npm 开发依赖审计的已知问题、Pages 属发布动作不在本地审计内。

因此 `RELEASE_AUDIT.md` **不是盲目自评**。它的缺陷是结构性的：「结论」列一律写"通过"，而限定条件被搬到文档末尾的独立小节，读者按表格读会得到与按全文读不同的结论。

**修改动作（替换 P1-14 第 2/3 条与 P0-7 第 2 条的一部分）**：

1. 成本更低的做法是**把已有披露上提**：将 README 那三句、以及中文单字切分的影响，搬进第 15 章正文对应小节（不必重写措辞，README 的原文可直接引用）。
2. `RELEASE_AUDIT.md` 改为在每一行的「结论」列内联限定，例如「通过（syntax-only 基线）」「通过（离线同义词代理）」，而不是把边界另置一节。「已知边界」小节保留，但不再承担"表格里没说的话"。

---

## 2. 结论强化：字数结论稳健，但数字应给区间，且审计行的问题是"换单位"

上一版把字数缺口写成单一数字（54,446 / 68.1%），并把 `RELEASE_AUDIT.md:7` 当作虚假陈述。重新按多种口径实测后，结论**方向不变但表述必须更精确**：

| 口径（`book/**/*.md`，排除 `.vitepress`） | 数值 | 占 8 万下限 |
| --- | --- | --- |
| 汉字，排除代码块（最严） | 54,446 | 68.1% |
| 汉字 + 中文标点，排除代码块 | 60,075 | 75.1% |
| 汉字 + 中文标点 + ASCII 词，排除代码块（最宽松的"字数"读法） | **62,662** | **78.3%** |
| 汉字，含代码块 | 54,967 | 68.7% |
| 原始字符数（含 Markdown 语法、代码、空白） | **94,011** | — |
| 去空白字符数 | 87,547 | — |

两个结论：

1. **缺口是稳健的。** 任何以"字"为单位的合理口径都低于 8 万，缺口区间为 **17,338–25,554 字**。上一版的判断成立，只是应当以区间呈现，并在修订时以最严口径（汉字）为目标，避免达标后又被口径争议推翻。
2. **`RELEASE_AUDIT.md:7` 不是伪造数据，是替换了计量单位。** `BOOK_CHARTER.md:72` 要求"中文 8–12 万**字**"，审计行写的是"正文与附录超过 8 万**字符**"——按原始字符 94,011，这句**字面为真**。这比"说假话"更隐蔽也更值得修：验收标准被一个单位替换悄悄满足了。

**修改动作（替换 P0-1 与 P0-7 中关于字数的部分）**：

1. 先在 `BOOK_CHARTER.md:72` 把口径钉死，建议原文：「字数以正文 Markdown（`book/**/*.md`，排除 `.vitepress`）中的汉字数计，排除代码块内容；下限 80,000，上限 120,000。统计脚本为 `scripts/wordcount.py`，其输出是唯一权威。」
2. 把第 8 节 G1 脚本落盘为 `scripts/wordcount.py`，`RELEASE_AUDIT.md:7` 的证据列改为引用该脚本的实际输出，禁止再出现"字符"这一单位。
3. 顺带修正同一文档的两处过时计数：`:9` 写 Northstar「10 项自动测试」，实测 13；`:10` 写 Linux「6 项测试」加 `:11` 的「4 项新增」合计 10，与实测一致，无需改。

---

## 3. 根因改写：不是"书没遵守自己的规范"，而是"规范层已识别问题、执行层为零"

上一版给出的根因一是"三种成熟度共用一个完成标签"，根因三是"缺少单一真相源"。这两条成立。但本轮读完 `reviews/TEST_PLAN_2026-08-23.md`（41 行）后，需要补一条**更准确、也更能指导修订**的根因，并据此改写上一版第 8、9 节的定位。

这份测试计划**已经逐条写明了我上一版当作"新增建议"提出的几乎全部内容**：

- 「提示注入不能改变检索策略、工具可见性或记忆写入」——即上一版 P0-3 要求补的注入测试。
- 「审批令牌绑定主体、任务、工具、参数散列和 TTL；过期及参数变化必须失败」——即 P0-4 的审批闭环。
- 「写工具重复调用满足幂等；执行后必须读取真实状态验证」——即 P0-4 的幂等与 verify。
- 「向量、图、重排故障时显式降级；权限服务故障时关闭访问」——即降级通道与 fail-closed。
- 「删除来源后块、向量、图、Wiki、缓存和记忆候选均按策略撤销」——删除级联，上一版**完全没提**。
- 「数据规格数量门：逻辑仓、ADR、Runbook、Schema、配置、工单和 Golden Questions」——即 P0-2 的数量门。
- 「6 个 Mermaid 图必须生成可访问 SVG，而非代码块」——即 P0-6，且它已经给出了"要 SVG 且要可访问"这一更高标准。
- 「LICENSE 与 LICENSE-CODE 使用官方完整文本」——即 P1-16。
- 「统一统计汉字、中文词、英文词、代码和引用的口径」——即本文件第 2 节的字数口径问题，**作者早已知道**。
- 「自动禁止'当前最新''完整实现''全部通过'等无时间或证据限定的绝对表述」——即 P2-1，且已提出用自动检查来防。
- 「fixture 路径必须在 CI 中完整执行」——见下面的 P0-10。

**这份计划的实现率为 0。** 于是根因应当改写为：

> **根因（修订）：这个仓库的规范层（宪章、案例规格、测试计划、自审报告）质量高且已经识别出几乎全部缺陷，缺的是执行层。四份规范性文档写得比多数正式出版物更严谨，但没有一条被转成可运行的检查。因此"书自己不遵守自己的规范"这一现象，准确说是"规范从未被执行过一次"。**

这条改写对修订工作有直接影响：**不要再新写计划。** 上一版第 8 节的 G1–G9 应当被定位为 `TEST_PLAN_2026-08-23.md` 的可执行实现，而不是另一套标准。

**修改动作**：

1. 在 `reviews/` 下新增 `TEST_PLAN_STATUS.md`，把 TEST_PLAN 的每条拆成一行，三列：条目、对应的门（G1–G9 或新增编号）、状态（`未实现 / 已实现 / 不适用`）。初始状态几乎全部为"未实现"——这就是修订的主清单。
2. 上一版第 9 节批次 1 增加一项：完成上述状态表并写入 `run_manifest.json`。
3. 凡 TEST_PLAN 已有条目，修订时**沿用它的措辞**，不要另造标准。它的标准比上一版更严的地方（例如 Mermaid 要求"可访问 SVG"、要求"键盘导航与对比度检查"）以它为准。

---

## 4. 新增问题（上一版遗漏）

### P0-10｜CI 从不运行测试，23 个测试从未在仓库外的环境跑过

**定位**：`.github/workflows/docs.yml`
**证据**：工作流只有两个 job——`build`（checkout → setup-node 22 → `npm ci` → `npm run docs:build` → upload-pages-artifact）与 `deploy`（deploy-pages）。**没有任何 Python 步骤**，没有 `unittest`，没有链接检查，没有 Mermaid 检查，没有字数检查。而 `TEST_PLAN_2026-08-23.md` 明确要求「fixture 路径必须在 CI 中完整执行；Linux 全仓路径至少验证 CLI 参数和小仓 fixture」，`BOOK_CHARTER.md:70-79` 也把"自动检查链接、引用、图表、代码与命令"列为完成标准。
**判断**：上一版只注意到"工作流存在但因无 Git 仓库而不会触发"，遗漏了更根本的一点——**即便有仓库，它也只发布站点，不验证任何东西**。这意味着全书 23 个测试、28 个代码块、52 个外链、6 张图，没有一项处在自动化保护之下。对一本主张"评测是一等公民"的书，这是与主题直接冲突的工程缺口，应定为 P0。
**修改动作**：

1. 在 `docs.yml` 前置一个 `test` job（`runs-on: ubuntu-latest`，`actions/setup-python@v5`，Python 3.12），执行：

```yaml
      - run: python3 -m unittest discover -s tests -v
        working-directory: examples/enterprise-case
      - run: python3 -m unittest discover -s tests -v
        working-directory: examples/linux-ebpf-case
      - run: python3 scripts/wordcount.py          # G1
      - run: python3 -m linux_kb ingest --help      # G6，参数契约
        working-directory: examples/linux-ebpf-case
```

2. `build` job 增加 `needs: test`；`build` 之后增加一步 `! grep -rl 'language-mermaid' book/.vitepress/dist/`（G2）。
3. 外链检查（G7）单独设一个 `schedule` 触发的 job（每周一次），不要放进 PR 路径——外链失败不应阻塞文档发布，但必须被发现。
4. 完成后，`RELEASE_AUDIT.md:14` 的「候选就绪」才可改为"通过"，且证据列必须写明 CI 里跑了哪几个门。

### P0-11｜本书旗舰能力问题无法被交付数据回答，而测试恰好绕开了这一点（P1-4 升级）

**定位**：`examples/enterprise-case/data/domain-model.json`、`data/relations.json`、`tests/test_domain_model.py`
**证据**（本轮逐字段核对，比上一版精确）：

- 领域模型声明 7 个 `entityTypes`（Service、Repository、API、Team、Runbook、Policy、RefundEvent）与 5 个关系（`CALLS`、`IMPLEMENTS`、`ON_CALL_FOR`、`DOCUMENTED_BY`、`GOVERNED_BY`）。
- `relations.json` 共 5 条边，用了 3 种类型：`CONSUMED_BY`×3、`DOCUMENTED_BY`×1、`AFFECTED`×1。其中 **`CONSUMED_BY` 与 `AFFECTED` 未在领域模型中声明**。
- 声明的 5 种关系里，**4 种零使用**（`CALLS`、`IMPLEMENTS`、`ON_CALL_FOR`、`GOVERNED_BY`）。
- 边的端点是实例 ID（`event-order-cancelled`、`code-refund-consumer`…），**从未绑定到任何 `entityType`**。`knowledge.json` 的 8 个对象也没有类型字段可供映射（键为 `acl, authority, citation, id, kind, system, tenant, text, title, version`，`kind` 的取值与 7 个 `entityTypes` 不对应）。
- 因此旗舰能力问题 **CQ-IMPACT-001**（"退款网关 API 变化会影响哪些服务、团队和运行手册？"，`requiredRelations` 为 `CALLS`/`IMPLEMENTS`/`ON_CALL_FOR`/`DOCUMENTED_BY`）**用交付的数据无法回答**：四种必需关系中只有一种存在。`CQ-POLICY-001` 需要 `GOVERNED_BY`，同样零数据。
- `tests/test_domain_model.py` 的三个断言全部是**模型对模型**的自校验：能力问题的 `requiredRelations` ⊆ 声明关系集合；关系端点 ⊆ `entityTypes`；`CALLS`/`GOVERNED_BY` 的 `temporal` 为真。**没有一个断言读取 `relations.json`。** 这正是违规能长期存活且测试全绿的机制。

**判断**：上一版以 P1 记为"自反矛盾"，评级偏低。第 8 章（5,816 字，全书最长）整章方法论的说服力就挂在这份数据上；能力问题是该章的核心方法（"从能力问题出发建模"），而交付的数据回答不了它自己写下的两个能力问题。这是对本书**方法论主张**的直接否证，属阻断级。
**修改动作**：

1. 新增 `tests/test_data_contract.py`，最少四条断言：`relations.json` 的类型集合 ⊆ 领域模型声明集合；每个实例 ID 能解析到一个 `entityType`；每个 `competencyQuestion` 的 `requiredRelations` 在 `relations.json` 中**都有至少一条实例边**；每条边的 `evidence_tier` ∈ 该关系的 `allowedEvidence`。
2. 按上述断言补数据：为 `CALLS`、`IMPLEMENTS`、`ON_CALL_FOR`、`GOVERNED_BY` 各补真实边；为 `CONSUMED_BY`、`AFFECTED` 在领域模型中补声明（含 `from`/`to`/`temporal`/`allowedEvidence`），或改用已声明类型表达同一语义。
3. 为 `knowledge.json` 每个对象补 `entity_type` 字段并与 7 个 `entityTypes` 对齐；`kind` 与 `entity_type` 的关系在第 8 章说明清楚。
4. 在第 8 章正文补一段"如何用测试守住领域模型"，把上面四条断言作为该章的收口产物。**这一步同时解决了 P1-6 的附录 D 缺评测资产问题的一部分**：它给出的是可复用的契约测试范式。

### P1-17｜证据分级框架被提出但没有贯穿正文

**定位**：全书；`book/appendices.md` 附录 A
**证据**：上一版把"证据分级"列为本书应当保护的核心贡献之一。本轮统计了它的实际使用密度，结论需要修正——它目前是**提出了而没有被使用**：

| 词 | 全书出现次数 |
| --- | --- |
| `resolved` | 5 |
| `deterministic` | 2 |
| `heuristic` | 2 |
| `inferred` | 2 |
| `asserted` | 1 |
| 「证据等级」 | 10 |
| 「证据分级」 | 0 |

五级英文词汇合计出现 12 次，分布在 54,446 字的正文里。相比之下"确定性"26 次、"推断"26 次、"观察"34 次，多数是普通用词而非该框架的术语用法——也就是说中英两套说法并未固定，读者无法判断"推断"是否等于 `inferred`。

**判断**：这不是错误，是**未兑现的杠杆**。这个框架是全书少数具备原创整合价值的装置，如果贯穿使用，它能同时解决"如何表达不确定性"和"如何让读者判断每条结论的可靠度"两个问题；停留在概念介绍层面则浪费了它。
**修改动作**：

1. 把它变成贯穿装置：正文凡给出一条关系、检索结果或架构结论，标注证据等级。第 10–13 章与第 15–17 章优先。
2. 附录 A 增加中英对照与判定流程（给出"拿到一条陈述，如何定级"的三到四步判定），并明确"推断/观察/确定性"等中文词在本书中是否等同于对应英文术语。
3. 与本文件修正 2 合并执行：先定枚举（含 `observed` 的归属），再全书贯穿，避免两次改词。

### P1-18｜体系化的主题缺口（七类），而它正是补足字数缺口的正确材料

**定位**：全书
**证据**：上一版只查了内部一致性，没有回答"相对于这个领域应有的内容，缺了什么"。本轮做了关键词覆盖扫描（`book/**/*.md`，格式为 词：出现次数）：

`token` 2｜`embedding` 0｜`吞吐` 0｜`冷启动` 0｜`索引重建` 0｜`PII` 0｜`GDPR` 0｜`多租户` 1｜`审计日志` 1｜`灰度` 1｜`人工复核` 1｜`时效` 1｜`分片` 1｜`删除权` 1｜`合规` 2｜`限流` 2｜`一致性` 2｜`压缩` 6

对照全书已覆盖得很好的部分（`冲突` 52、`治理` 33、`成本` 28、`租户` 27、`角色` 25、`回滚` 18、`缓存` 19），缺口集中在**运营与经济性**这一侧：

1. **上下文窗口预算与 token 成本经济学**——一本讲"给智能体供给上下文"的书，`token` 只出现 2 次，没有讨论供给多少、如何取舍、成本如何随规模变化。这是最显眼的缺口。
2. **上下文压缩与摘要策略**——`压缩` 6 次、分布 3 个文件，没有独立处理。
3. **多租户隔离作为一等主题**——`租户` 作为字段出现 27 次，但`多租户` 仅 1 次，隔离模型、跨租户泄漏、按租户的索引与配额均未讨论。
4. **数据保留、删除权与合规级联**——`GDPR` 0、`PII` 0、`删除权` 1、`保留期` 4。而 `TEST_PLAN_2026-08-23.md` 已经要求"删除来源后块、向量、图、Wiki、缓存和记忆候选均按策略撤销"——**测试计划里有，正文里没有对应章节**。
5. **索引重建、冷启动与回填运维**——`索引重建` 0、`冷启动` 0。派生物"可删除可重建"是全书反复强调的原则，但重建的代价、顺序与在线切换从未展开。
6. **人在环与审计留痕**——`人工复核` 1、`审计日志` 1、`灰度` 1。第 12 章讲了行动边界，但谁批准、留什么痕、如何回溯审计没有系统处理。
7. **容量与性能工程**——`吞吐` 0、`限流` 2、`分片` 1。有延迟（16 次）但没有吞吐与容量。

**判断**："体系化"的缺口不在骨架，而在这七个运营主题。它们都不是可选的边角内容——企业上下文一旦上线，这七项就是运维会议上的全部议题。
**修改动作**：

1. 按每主题 2,500–3,500 字规划，七个主题合计 **17,500–24,500 字**，与第 2 节测得的字数缺口 **17,338–25,554 字** 高度吻合。**用这七个主题补足字数，不要扩写现有议论。** 这一条替换上一版 P0-1 中"补足缺口"的笼统说法。
2. 安放位置建议：主题 1、2 进第三部分（供给与检索）；主题 3、4、6 进第五部分或新增一章"运营与合规"；主题 5、7 进第四部分实践，正好同时缓解 P1-1 的结构失衡（第四部分从 15.2% 提到 30% 以上）。
3. 主题 4 必须与 `TEST_PLAN` 的删除级联条目对齐，并落一条对应测试；否则又会形成"计划有、正文无、测试无"的第三次断裂。

---

## 5. 对上一版第 9 节执行顺序的修订

只列变更，其余批次内容不变。

| 批次 | 变更 |
| --- | --- |
| 批次 0 | 不变（P0-9 建 Git、P0-6 修 Mermaid、P1-16 补许可证全文）。P0-6 的验收标准提高为 TEST_PLAN 的原文要求：**生成可访问 SVG**，含替代文本。 |
| 批次 1 | 增加：产出 `reviews/TEST_PLAN_STATUS.md`（见第 3 节），并在 `BOOK_CHARTER.md:72` 钉死字数口径、落盘 `scripts/wordcount.py`。P0-1 的措辞按第 1 节修正 1 改写；`RELEASE_AUDIT.md` 按第 1 节修正 3 改为行内限定；顺带修 `:9` 的测试数 10→13。 |
| 批次 2 | 增加两项：**P0-10**（CI 增加 `test` job 并前置于 `build`）、**P0-11**（数据↔领域模型契约测试 + 补齐关系数据）。P1-13 第 1 条按修正 2 改写（`certainty` 改名而非改数值口径）。P1-14 第 2/3 条按修正 3 改为"上提 README 的既有披露"。 |
| 批次 3 | 不变。新增 `test_data_contract.py` 可与 P0-11 合并在批次 2 完成，不必等到批次 3。 |
| 批次 4 | P0-1 的补写内容改为**按 P1-18 的七个主题**执行，字数目标以 `scripts/wordcount.py` 的汉字口径为准（下限 80,000）。P1-1 的结构配平与主题安放合并考虑。 |
| 批次 5 | 增加 **P1-17**（证据分级贯穿正文 + 附录 A 中英对照与判定流程），与 P1-5 的术语统一合并执行以免两次改词。 |
| 批次 6 | 增加：`TEST_PLAN_STATUS.md` 全部条目为"已实现"或"不适用"，方可把 `run_manifest.json` 的 `verdict` 改为 `cleared`。 |

---

## 6. 本轮新增的验证记录

全部命令于 2026-08-27 在仓库内实际执行。

| 项 | 方式 | 结果 |
| --- | --- | --- |
| 仓库是否变动 | `find -printf '%TY-%Tm-%Td %TH:%TM'` 排序 | 最新非评审文件 2026-08-25 00:11，报告成稿后无改动 |
| 多口径字数 | 自写脚本，四种口径 | 54,446 / 60,075 / 62,662 / 94,011（详见第 2 节） |
| `examples/` 全量清单 | `find` + `wc -l` | 25 个文件；Python 共 1,089 行；enterprise-case `src/` 仅 2 文件 301 行，无 REST/MCP 入口 |
| Docker 配置 | 读 `Dockerfile`、`docker-compose.yml` | 存在且质量良好：digest 固定、`network_mode: none`、`read_only`、`tmpfs` |
| 降级披露 | 读 `examples/enterprise-case/README.md`、`RELEASE_AUDIT.md:17-22` | 已披露语义通道、任务记忆、syntax-only 基线、9,632 未解析候选 |
| 领域模型 vs 数据 | `json.load` 后集合比对 | 声明 5 关系 / 数据用 3 种；`CONSUMED_BY`、`AFFECTED` 未声明；4 种声明关系零使用；实例无 `entityType` 绑定 |
| 能力问题可答性 | 比对 `requiredRelations` 与实例边 | CQ-IMPACT-001 四种必需关系仅 1 种有数据；CQ-POLICY-001 零数据 |
| `certainty` 取值 | 枚举 5 条边 | `resolved`×3、`asserted`×2，**字符串非数值**（修正上一版错误） |
| `allowedEvidence` 取值 | 枚举 5 个关系 | `deterministic`/`resolved`/`asserted`/**`observed`**；正文的 `heuristic`、`inferred` 不在其中 |
| 测试性质 | 读 `test_domain_model.py` 全文 | 三个断言均为模型对模型自校验，未读取 `relations.json` |
| 引用校验测试强度 | 读 `test_context_demo.py:27-30` | 仅断言 citation 含 `@`，因此 `context_demo.py:53` 覆盖数据自带 citation 的缺陷不会被捕获 |
| CI 内容 | 读 `.github/workflows/docs.yml` 全文 | 仅 build + deploy，无 Python、无测试、无链接/图表/字数检查 |
| 既有测试计划 | 读 `reviews/TEST_PLAN_2026-08-23.md` 全文 | 41 行，已覆盖注入、审批令牌、幂等、降级、删除级联、数量门、Mermaid SVG、许可证全文、字数口径统一、绝对表述禁用；实现率 0 |
| 主题覆盖 | 40 个关键词计数 | 见 P1-18；`embedding`/`吞吐`/`冷启动`/`索引重建`/`PII`/`GDPR` 均为 0 |

### 结语

换一轮独立取证后，**判定不变，但对这本书的评价方向要调高一档，对修订难度的评估要调低一档。**

调高的理由：`TEST_PLAN_2026-08-23.md`、`RELEASE_AUDIT.md` 的「已知边界」、`examples/enterprise-case/README.md` 的实现边界说明、digest 固定且网络隔离的 Docker 配置——这四处显示作者对自己交付物的边界有清晰且诚实的认知，识别出的问题清单与我两轮独立评审的结论高度重合。这不是一份自我感觉良好的稿子。

调低的理由：既然规范层已经把问题列清楚了，修订工作的性质就从"重新设计"变成"逐条兑现"。真正需要新增创造性内容的只有两处——P1-18 的七个运营主题（同时解决字数与结构失衡），以及 P1-17 把证据分级贯穿正文。其余全部是执行：建 Git、修 Mermaid、CI 跑测试、补数据到契约、把已有披露上提、把单位与状态钉死。

一句话给下游模型：**这本书缺的不是判断力，是一次完整的执行。先读 `TEST_PLAN_2026-08-23.md`，把它变成 CI 里跑得起来的东西，其余问题会跟着塌缩。**

—— 复核完毕。修正 3 项、升级 1 项、新增 3 项，修正后合计 30 项（P0 十一项、P1 十七项、P2 两项）。



---

# 卷三 · 第三轮复核（对卷二的审计·最终裁定）

差异汇总：**1 项重大撤回（P1-18 的七类主题缺口大部分不成立）、1 项连带修订（批次 4 的补字数策略必须改）、其余全部维持。** 修订后合计 30 项不变，但 P1-18 降级收窄。

---

## 1. 事实基础复核：仓库仍未变动，全部测量复现一致

除 `reviews/` 下的两份评审文件外，仓库自 2026-08-25 00:11 后没有任何文件改动。本轮重新执行的回归测量与前两轮完全一致：正文汉字 54,446（排除代码块）；测试 13 + 10 = 23 全绿；`dist/` 中 10 个文件仍含 `language-mermaid`；`git` 仍不存在。**前两轮所有基于文件状态的结论，其证据基础均成立。**

本轮重点不是重测，而是审计第二轮复核（卷二）自身的推理质量。结论：它的修正 1–3、第 2 节字数口径、第 3 节根因改写、P0-10、P0-11、P1-17 全部经得起复核；**P1-18 经不起。**

---

## 2. 撤回：P1-18 的"七类运营主题缺口"大部分不成立

### 2.1 错误机制

卷二 的 P1-18 用关键词扫描推断主题缺失，但**扫描词表以英文术语和窄口径中文词为主，而这本书通篇用中文术语写作**。它数了 `embedding`（0 次）却没数「嵌入」（19 次）；数了 `token`（2 次）却没意识到全书把 token 写作「Token 预算」「上下文预算」（「预算」20 次、「窗口」17 次）；数了「索引重建」（0 次）却没数「重建」（33 次、14 个文件）；数了 `GDPR`/`PII`（0 次）就断言删除合规无正文，却没查「tombstone」「删除传播」「撤销」（15 次）。**测量本身是准的，推断是错的。**

### 2.2 逐主题重判（中文语境逐条核对后）

| 原 P1-18 主题 | 重判 | 关键证据 |
| --- | --- | --- |
| 1. 上下文预算与 token 经济 | **大部分已覆盖** | ch04:31 论证为何不能塞满窗口并给出组装配额；ch05 重排成本与预算内选择；ch10:83 Context API 要求表达"上下文预算"；**ch10:117 按阶段拆分成本模型并用消融淘汰组件**；ch13:79 摄取/存储/查询成本拆解；ch15:108 Token 预算下的证据选择器；ch17:37「预算是产品行为的一部分」。真正缺的只有**定量部分**：成本随规模的曲线、每通道单位成本的数量级、预算分配的可算例子 |
| 2. 压缩与摘要策略 | **已覆盖** | 「摘要」88 次、18 个文件；层级摘要（RAPTOR 式）本就是第 5、7 章的主线之一 |
| 3. 多租户隔离 | **已覆盖，且质量高** | ch09:21「必须在物理或逻辑索引层保证隔离，不能依赖提示词」；ch12:77 跨租户安全回归；ch14:48 案例专设第二租户验证隔离；ch17:123 跨租户泄漏对抗场景 |
| 4. 删除权与合规级联 | **正文已覆盖，卷二 的"正文里没有"判断错误** | ch11:88 完整给出 tombstone→撤销版本→隔离索引投影→页面过期→清缓存→按法规安排物理清除的全链条，含审计日志保留策略；ch11:90「删除传播测试应成为安全回归的一部分」；ch13:35 把"删除传播时间"列为可测量指标；ch15:136 增量摄取实现 tombstone。缺的只是**法规命名层**（GDPR、数据主体请求、保留期时刻表未点名） |
| 5. 索引重建与回填运维 | **部分覆盖** | ch11:74 血缘支撑"定向重建"、否则退化为全量重建；ch15:136「只有受影响向量和全文文档重建」；ch16:71 重建队列与 stale 传播。缺的是**运维侧**：冷启动、回填顺序、在线切换、重建期间的服务降级 |
| 6. 人在环与审计留痕 | **已覆盖** | 「审批」24 次、「审计」38 次、「确认」36 次；ch17:91 确认令牌绑定用户/工具/参数散列/短有效期；ch11:104 双时间轴审计回放 |
| 7. 容量与性能工程 | **确实缺失，维持原判** | 「吞吐」0、「压测」0、「TPS/每秒」0、「QPS」1、「容量」4。全书有延迟与 SLO，无容量规划、压测方法与吞吐设计 |

### 2.3 修订后的 P1-18（收窄版）

真实缺口从七类收窄为 **一类整缺 + 两个半缺**：

- **P1-18a（维持 P1）容量与性能工程**：新增一节（建议放第 13 章或第 17 章），覆盖容量估算（对象数 × 通道 × 版本保留的存储模型）、查询吞吐设计、压测方法与指标、限流与背压。约 2,500–3,500 字。
- **P1-18b（降为 P2）成本的定量化**：第 10/13 章的成本模型已有骨架，补一个可算例子（给定文档量与查询量，各通道的月成本量级估算表）即可，约 1,000–1,500 字。
- **P1-18c（降为 P2）删除合规的法规命名 + 重建运维**：ch11 已有机制，补一段把机制映射到 GDPR/数据主体请求/保留期的表述，加一小节重建运维（冷启动/回填/在线切换），合计约 2,000–3,000 字。

**修改动作（连带修订批次 4）**：卷二 第 5 节批次 4 中「按 P1-18 的七个主题补 17,500–24,500 字」**作废**。收窄后的 a/b/c 三项合计只有约 5,500–8,000 字，字数缺口（17,338–25,554）的主体必须回到第一份报告 P1-1 的原方案：**深写第四部分的工程实践**——把批次 2/3 产生的真实实现（写行动闭环、契约测试、Golden Questions、数据扩充）转写为正文，这正好同时解决结构失衡（第四部分 15.2% → 30%+）与字数缺口，且不会为凑字数而写正确性存疑的新理论。

---

## 3. 对其余结论的抽查确认（本轮实际复核过、维持原判的）

- **P0-11 维持**：重新加载 `domain-model.json` 与 `relations.json` 比对，声明 5 关系/数据用 3 种、`CONSUMED_BY`+`AFFECTED` 未声明、CQ-IMPACT-001 四种必需关系仅 1 种有数据——全部复现。
- **P0-10 维持**：`docs.yml` 全文只有 build + deploy，无任何测试步骤。
- **修正 2（`certainty` 为字符串枚举）维持**：5 条边取值 `resolved`×3、`asserted`×2。
- **修正 3（披露已存在）维持**，且本轮发现它比 卷二 说的还充分：ch14:29 正文其实已有「验证删除来源后派生物是否消失」的表述，进一步支持"上提/交叉引用既有内容"优于"新写"。
- **P1-17（证据分级未贯穿）维持但注意**：中文「证据等级」出现 10 次，说明框架在正文有中文承载，只是密度仍低且中英对应未固定。修改动作不变。
- **根因改写（规范层优秀、执行层为零）维持**：`TEST_PLAN_2026-08-23.md` 实现率仍为 0。

## 4. 给后续评审轮次的方法论教训

记录在案，防止第四轮再犯：**对中文书稿做主题覆盖分析时，禁止以英文关键词计数作为"缺失"的充分证据。** 正确流程是：英文词 + 中文同义词族并扫 → 对命中为零的主题再做一次概念级抽查（读相关章节的小节标题与段落）→ 只有两级都空才可判"缺失"。本书用「嵌入」不用 embedding、用「Token 预算」不用 token cost、用「删除传播」不用 GDPR——第二轮正是在这里跌倒的。

### 结语

三轮评审、三个模型，判定收敛且稳定：**不通过 v1.0，缺的是执行而非判断力。** 本轮的主要贡献是把第二轮对"体系化覆盖"的悲观评估纠正回来——这本书的主题覆盖比第二轮所说的完整得多，多租户、删除级联、人在环、预算约束都有质量不低的正文；真正整块缺失的只有容量与性能工程。这进一步支持第二轮结语的方向判断：评价再调高半档，修订工作量再调低一档。下游模型执行时，以本文件第 2.3 节替换 卷二 的 P1-18 与批次 4，其余按 卷二 第 5 节执行。

—— 第三轮复核完毕。撤回 1 项主体、收窄为 1×P1 + 2×P2，其余 29 项维持。
