# 第 18 章 构建 Linux eBPF 知识库

> 本章要回答：如何把企业上下文方法应用到真实规模、持续演化的 Linux 内核代码库？

eBPF（extended Berkeley Packet Filter）是一种让受约束程序在 Linux 内核中运行的机制。用户态先把程序装载进内核；verifier 在执行前验证程序的控制流与内存访问，通过后程序可以被即时编译（JIT）并挂接到内核事件点（hook）。map 是 eBPF 程序之间以及程序与用户态之间共享数据的结构。理解“装载—验证—执行—挂接”和 map 这两条主线，就足以跟随本章；CO-RE、libbpf、BTF 与 Kconfig 会在需要时说明。[Linux BPF 文档](https://docs.kernel.org/bpf/)

Northstar 证明了企业上下文的完整生命周期，Linux 内核则检验代码知识库能否面对真实规模、宏、条件编译、函数指针、跨目录调用和长期演化。本章选择 eBPF 子系统作为第一块范围：它拥有清晰的用户态入口、复杂的 verifier、丰富的 map 与程序类型、BTF 结构信息以及大量官方文档，适合同时演示文本、代码、图和层级 Wiki。

目标不是让模型“读懂整个 Linux”，也不是生成一套替代内核文档的解释。第一版要建立一个作者可长期使用的研究工具：固定上游版本，回答一组机制问题，所有结论回到源码或官方文档，并明确静态解析无法证明的关系。

## 18.1 固定研究快照

案例不把 Linux 源码复制进书籍仓库。读者从上游获取指定 tag，并记录解析后的提交：

```bash
git clone --depth 1 --branch v6.12 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux
git rev-parse HEAD
```

若远端支持 partial clone，可以增加 `--filter=blob:none` 节省初始带宽；部分镜像不支持过滤时，以上浅克隆命令更稳定。

示例以长期存在的稳定 tag `v6.12` 作为可复现基线；读者可以替换为更新版本，但必须生成新的 Snapshot Manifest 和测试期望。不要引用浮动的 `master`，否则路径、行号和机制会随提交变化。

Manifest 记录远程仓库、tag、commit、配置、编译器、解析器、Tree-sitter grammar、BTF 产物和生成时间。源码引用使用：

```text
code://linux/kernel@<commit>/kernel/bpf/syscall.c#<symbol>
```

显示层可将它渲染为上游网页链接与行区间；内部证据仍绑定提交和内容散列。若同一符号在新 tag 中变化，逻辑 ID 保持，版本 ID 更新。

## 18.2 划定子系统边界

核心摄取范围从 `kernel/bpf/` 开始，并按问题扩展到：

- `include/linux/bpf*.h` 与 `include/uapi/linux/bpf.h`；
- `net/core/filter.c` 等程序类型与 helper 实现；
- `kernel/trace/`、网络与 cgroup 等 attach hook；
- `tools/lib/bpf/` 和必要的 bpftool 用户态路径；
- `Documentation/bpf/` 官方文档；
- 自测目录 `tools/testing/selftests/bpf/`。

不能简单递归摄取所有被 include 的文件，否则边界迅速扩展为全内核。系统维护“核心、必要依赖、外部引用”三种范围。核心对象完整解析和生成 Wiki；必要依赖保存相关符号；外部引用只建 stub 与回跳，按查询需要再扩展。

范围策略由验收问题驱动。研究程序加载需要 syscall、对象、verifier 与程序类型；研究 attach 需要链接和 hook；研究 CO-RE 需要 BTF 与 libbpf。一个新问题若持续需要外部模块，再通过显式配置扩大边界。

## 18.3 eBPF 领域对象模型

这一节应用第 8 章的三层方法。概念层把“程序加载后经过验证并挂接到内核 hook”描述成领域机制；逻辑层定义 `ProgramType`、`VerifierPhase`、`AttachType` 等稳定类型及其关系契约；物理层才把它们投影成 SQLite 行、图节点、BM25 字段和 Wiki 页面。Tree-sitter 或 BTF 的输出是源映射，不是领域本体本身。

通用代码节点包括仓库、目录、文件、符号、类型、宏、配置和测试。eBPF 还需要领域节点：

- `SyscallCommand`：`BPF_PROG_LOAD`、`BPF_MAP_CREATE` 等命令；
- `ProgramType`：不同程序类型及其操作集合；
- `MapType`：map 实现、操作和生命周期；
- `Helper` 与 `Kfunc`：程序可调用能力及约束；
- `VerifierPhase`：控制流、状态传播和安全检查；
- `BTFType`：类型、函数、变量和行信息；
- `AttachType` 与 `Hook`：程序挂载位置；
- `Selftest`：验证机制与回归场景。

关系包括 `DEFINED_IN`、`CALLS_CANDIDATE`、`CALLS_RESOLVED`、`DISPATCHES_TO`、`VALIDATED_BY`、`USES_MAP_TYPE`、`ATTACHES_TO`、`DESCRIBED_BY` 和 `TESTED_BY`。领域关系使查询不必把所有机制退化为函数名相似度。

每种关系还应像 Northstar 模型一样定义主客体类型与证据门槛。例如 `CALLS_CANDIDATE(Symbol, Symbol)` 可以来自语法解析，只用于探索；`CALLS_RESOLVED(Symbol, Symbol)` 必须附带编译配置和解析器证据；`TESTED_BY(Mechanism, Selftest)` 需要可定位的测试引用。全内核对象模型不是另起炉灶，而是对通用 `Repository`、`File`、`Symbol`、`Evidence` 和 `Snapshot` 类型的领域扩展。

节点与边都保留编译配置。例如某调用或类型只在 `CONFIG_BPF_SYSCALL` 下存在，引用必须说明条件。Linux 并不存在唯一调用图；不同架构与 Kconfig 产生不同可达代码。

## 18.4 采集流水线

第一步扫描 Git 树并为文件建立版本对象。第二步用 Tree-sitter C 解析语法树，抽取函数定义、声明、结构体、枚举、宏引用、include 和语法调用。Tree-sitter 支持增量解析并可为多种语言提供具体语法树，适合构建跨语言候选结构。[Tree-sitter](https://tree-sitter.github.io/tree-sitter/)

第三步读取构建信息与 Kconfig，给对象添加编译条件。第四步在可构建环境中生成编译数据库或使用 clang tooling，解析更精确的符号与类型。第五步读取 `vmlinux` BTF，补充内核最终产物中的类型、函数、变量和行信息。

官方文档说明 BTF 是用于描述 BPF 程序与 map 相关调试信息的元数据格式，并定义了 `.BTF` 与 `.BTF.ext` 中的类型、函数和行信息。[Linux BTF 文档](https://docs.kernel.org/bpf/btf.html) 它能验证某些类型和函数确实进入目标内核产物，但不等于完整调用图。

第六步摄取 `Documentation/bpf` 与 selftests。文档按标题层级解析，测试关联目标 helper、map 或 verifier 行为。最后生成对象清单、倒排索引、图边、Wiki 输入和误差报告。

## 18.5 Tree-sitter、LSP、SCIP 与 ArtifactFS 的分工

Tree-sitter 适合快速、离线、跨版本地恢复语法结构，即使代码不能完整编译也能工作。它看到 `foo(x)`，却未必能在宏、函数指针和条件编译下确定唯一目标，因此关系应标为候选。

LSP 适合交互式定义、引用、类型和诊断，但通常依赖一个配置好的工作区进程。它可以成为精确导航工具，不应成为唯一持久索引。SCIP 之类协议可以把语言索引器生成的定义与引用持久化为语言无关数据，适合离线查询和跨仓关联。[SCIP](https://github.com/scip-code/scip)

ArtifactFS 是这里对版本化源码工件层的抽象：按仓库和提交保存或访问不可变 blob，并提供路径、行和散列。它不必是特定产品，可以由本地 Git 对象库、对象存储或源码归档实现。最终证据来自 ArtifactFS，而不是 LSP 进程或模型摘要。

组合关系是：Tree-sitter 提供广覆盖候选，编译器/SCIP/BTF 提高确定性，LSP 支持在线探索，ArtifactFS 保留事实。任何单一工具都无法承担全部职责。

## 18.6 建立 eBPF 图

`bpf()` 系统调用分派是第一条验收路径。系统从 UAPI 中的 `enum bpf_cmd` 建立命令节点，从 `kernel/bpf/syscall.c` 抽取分派与处理函数，把 `BPF_PROG_LOAD` 连接到程序加载逻辑，再连接 verifier 和对象生命周期。宏展开或函数指针无法静态确认时，路径边显示证据等级。

map 路径连接创建命令、map type、`map_alloc`/`map_free` 等操作、文件描述符和用户态访问。Linux 文档将 BPF map 描述为内核中的通用数据结构，用于 BPF 程序与用户态之间共享数据，也可在程序之间共享。[BPF maps](https://docs.kernel.org/bpf/maps.html) 图应进一步以源码验证具体实现，而不是只复制定义。

verifier 路径从程序加载进入检查阶段，连接指令、控制流、寄存器状态、栈状态和 helper 约束。官方文档说明 verifier 会遍历可能路径并跟踪寄存器和栈槽状态；文档适合建立机制地图，源码和 selftests 用于版本化细节。[BPF verifier](https://docs.kernel.org/bpf/verifier.html)

attach 路径跨出 `kernel/bpf/`，连接 link、program type、attach type 和具体 hook。这证明每个仓库或目录只是子图，真实机制通过稳定领域实体连接。

## 18.7 生成层级 Wiki

Wiki 顶层是“eBPF 子系统地图”，说明用户态加载、验证、map、执行与 attach 的总体关系。第二层按机制划分：syscall、program、map、verifier、BTF、link/attach、JIT 与 selftests。第三层是源码模块，第四层是关键符号。

每张机制页使用统一 Schema：目标、入口、核心对象、阶段、关键关系、配置条件、失败方式、测试、源码引用和已知不确定性。模板先从图填充入口与关系，再由模型可选生成解释。任何段落都保存输入证据。

高层页面不复制整个源码。询问“verifier 为什么要做状态剪枝”时，页面提供机制解释和入口；继续追问具体等价判断时，再下钻到函数与源码。层级路由让用户在正确抽象层停留。

页面的 `freshness` 由输入提交决定。切换到新 tag 后，变更文件使相关符号、模块和机制页失效；未变化的官方概念页可以复用，但其源码引用仍生成新快照验证。

## 18.8 横向混合、纵向下钻

查询“BPF 程序加载时如何被 verifier 检查”先由 Wiki 向量命中程序加载与 verifier 页面，BM25 命中 `BPF_PROG_LOAD`，图连接命令、处理函数和 verifier 入口。上下文包返回一条高层路径及每一步源码证据。

查询具体符号使用 BM25 和代码索引优先；查询“修改某状态合并逻辑影响哪些测试”以符号为图种子，沿调用、模块与 `TESTED_BY` 扩展；查询“map 如何连接用户态和程序”同时使用官方文档、系统调用与 map 操作图。

三条横向通道共享版本范围，纵向层级从子系统、机制、模块到符号。最终结果始终返回 `repository + tag/commit + path + lines/symbol`。摘要回答“是什么与为什么”，源码回答“这个版本具体如何实现”。

## 18.9 可复现实作接口

在 `examples/linux-ebpf-case/` 目录运行以下接口。`--scope` 接受可重复的 glob；省略它时使用内置 eBPF 范围：

```bash
python3 -m linux_kb ingest \
  --repo /path/to/linux \
  --ref v6.12 \
  --output generated/ebpf-v6.12 \
  --scope 'kernel/bpf/**/*.c' \
  --scope 'include/uapi/linux/bpf.h' \
  --scope 'Documentation/bpf/**/*.rst'

python3 -m linux_kb build-wiki --snapshot generated/ebpf-v6.12

python3 -m linux_kb query \
  "BPF_PROG_LOAD 如何进入 verifier？" \
  --snapshot generated/ebpf-v6.12

python3 -m unittest discover -s tests -v
```

这些命令需要本地已有 Linux checkout；仓库自带 `fixtures/linux/` 只用于解析器单元测试，不足以复现完整子系统图。

首版实现可以只依赖 Git、Python 与可选 Tree-sitter；没有 clang/BTF 时生成 `syntax-only` 快照，查询明确显示精度降级。启用编译产物后生成 `compiled` 快照，并运行两者差异报告。

输出目录只保存可重建索引和 Wiki，不提交 Linux 源码。测试使用几份兼容许可证的小型 fixture 验证解析器，真实集成测试在用户本地 Linux checkout 上运行。

## 18.10 验收问题与误差报告

第一版验收覆盖五组问题：

1. `BPF_PROG_LOAD` 从用户 ABI 到 verifier 的主要路径；
2. verifier 如何表示并传播寄存器与栈状态；
3. map 从创建、文件描述符、程序访问直到释放的生命周期；
4. BTF 类型、函数和行信息如何映射到固定源码；
5. 修改关键符号可能影响哪些模块、配置与 selftests。

每题标注必要节点、路径、文档和源码引用。测试不要求模型使用固定措辞，而要求路径中的确定边有证据，候选边标明不确定性，引用可在指定提交解析。

误差报告至少列出：语法解析失败文件、未解析调用、同名符号歧义、函数指针候选、宏产生关系、受条件编译影响对象、BTF 未覆盖对象和外部范围 stub。覆盖率不能把候选边计作精确边。

人工抽样比较 Tree-sitter 候选与编译级关系。结果按直接调用、宏、函数指针和跨配置分桶。这份报告比一张看似完整的大图更重要，因为它告诉研究者哪些路径可以信任。

## 18.11 扩展到全内核

全内核不能只把当前脚本指向仓库根目录。它需要按 MAINTAINERS、Kconfig、目录和构建目标划分子系统子图，以稳定符号、头文件、配置和调用关系连接。层级路由先选择子系统，再进行局部检索。

存储按提交增量更新。Git diff 识别变化文件，解析器更新受影响符号，反向关系找出需要复核的调用者和 Wiki。公共头文件与核心 API 变化可能扇出巨大，应进入高优先级影响队列，而不是同步阻塞所有页面。

索引分为当前快照和历史冷层。常用 release 保持完整可查询，任意提交按需构建。源码 blob 由 Git 去重，向量与摘要按内容散列复用。容量规划分别计算文件、符号、边、嵌入和 Wiki，而不是以仓库大小粗略估计。

跨版本查询是全内核知识库的独特价值：一个机制何时引入、符号职责如何变化、旧文档为何不再适用。它要求逻辑身份映射和 diff 证据，不能仅比较两次模型摘要。

## 本章小结

Linux eBPF 案例把代码知识库的二维设计落到真实源码：横向组合 BM25、摘要向量与关系图，纵向从子系统逐层下钻到版本化源码。Tree-sitter 提供广覆盖候选，编译信息、SCIP 与 BTF提高确定性，LSP 服务交互，ArtifactFS 保存最终证据。领域对象、配置条件和误差报告防止图谱伪装成完整真相。按固定 tag、可重建 Manifest 和验收问题实施后，这套方法可以逐步扩展到完整 Linux 内核。

本书进一步对完整 Linux `v6.12` 执行了全仓 SQLite 建模与六组跨子系统查询，参见[番外：为完整 Linux 内核建立代码知识库](/extras/full-linux-kernel)。

## 延伸阅读

- Linux Kernel Documentation, [BPF subsystem](https://docs.kernel.org/bpf/)。
- Linux Kernel Documentation, [BPF maps](https://docs.kernel.org/bpf/maps.html)。
- Linux Kernel Documentation, [eBPF verifier](https://docs.kernel.org/bpf/verifier.html)。
- Linux Kernel Documentation, [BPF Type Format](https://docs.kernel.org/bpf/btf.html)。
- Tree-sitter, [Documentation](https://tree-sitter.github.io/tree-sitter/)。
- SCIP contributors, [SCIP](https://github.com/scip-code/scip)。
