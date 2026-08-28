# Linux 案例选题：eBPF 与调度器

> 文档类别：案例范围决策记录。

## 结论

第一版选择 **eBPF** 作为 Linux 内核知识库案例，调度器保留为后续扩展主题。

## 比较

| 维度 | eBPF | 调度器 |
|---|---|---|
| 边界 | `kernel/bpf`、`include/*/bpf*`、文档、工具和挂载点，虽跨子系统但有明确核心 | `kernel/sched` 核心集中，但与进程、时钟、拓扑、cgroup、锁和架构代码深度耦合 |
| 知识形态 | syscall、程序类型、map、helper、verifier、BTF、JIT、hook，节点和关系丰富 | 调度类、runqueue、task、策略、时钟和拓扑，算法关系密集 |
| 学习路径 | 用户态程序→syscall/libbpf→verifier→map/helper→hook，容易形成端到端问题 | 需要先理解调度理论、并发与硬件拓扑，入口对初学者更分散 |
| 代码知识库展示力 | 可展示源码、类型、调用、配置、文档、用户态/内核边界和运行时对象 | 特别适合展示算法演进、历史版本和高复杂度调用关系 |
| 结构化元数据 | BTF 提供类型、函数和源码行信息，可与静态索引交叉验证 | 主要依赖 C 解析、编译信息和 tracepoint，缺少同等集中的领域元数据 |
| 当前变化 | 活跃演进，版本固定和差异知识很重要 | CFS 正向 EEVDF 过渡，历史解释价值很高但增加首版范围 |

Linux 官方文档将 BPF map 描述为内核与用户态共享数据的通用存储，并记录多种 map 类型；verifier 需要遍历程序路径并跟踪寄存器和栈状态；BTF 还携带类型、函数与源码行信息。这使 eBPF 同时具有文档知识、源码结构、语义关系、运行时对象和安全规则，适合作为企业上下文方法的压力测试。[BPF maps](https://docs.kernel.org/bpf/maps.html) · [Verifier](https://docs.kernel.org/bpf/verifier.html) · [BTF](https://docs.kernel.org/bpf/btf.html)

调度器同样有很高价值。官方文档显示调度类通过 `sched_class` hooks 连接核心调度行为，而 Linux 从 6.6 开始由 CFS 向 EEVDF 过渡。它更适合未来单独展示“历史版本与算法语义知识库”。[CFS](https://docs.kernel.org/scheduler/sched-design-CFS.html) · [EEVDF](https://docs.kernel.org/scheduler/sched-eevdf.html)

## eBPF 第一版边界

- 固定一个发布时稳定的 Linux tag，正式写作时记录 commit SHA；
- 核心源码从 `kernel/bpf/` 开始，按问题扩展到头文件、网络/cgroup/tracing hook 和 `tools/lib/bpf`；
- 首批实体：syscall command、program type、map type、helper/kfunc、verifier phase、BTF type、hook、source symbol；
- 首批关系：creates、loads、verifies、calls、attaches-to、stores-in、described-by、defined-at；
- 所有 Wiki 陈述回到官方文档或 `tag + path + lines`；
- Tree-sitter 关系标为语法候选，编译/BTF 结果标为解析后或精确关系。

## 代表性验收问题

1. 一个 BPF 程序从用户态加载到成功 attach 经过哪些内核路径？
2. verifier 如何跟踪指针和 map value，关键状态结构在哪里定义？
3. BTF 如何把运行时对象连接回类型、函数和源码行？
4. 某 map type 的创建、访问、生命周期和支持 helper 分别在哪里实现？
5. 修改 verifier 中一个检查可能影响哪些程序类型、selftests 和文档？
