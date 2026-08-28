# Linux v6.12 集成运行报告

运行日期：2026-08-23

## 快照

- 上游：`https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`
- ref：`v6.12`
- commit：`adc218676eef25575469234709c2d87185ca223a`
- 模式：`syntax-only`
- 范围：`kernel/bpf/*.c`、`include/uapi/linux/bpf.h`、`Documentation/bpf/*.rst`

## 产物规模

| 指标 | 数量 |
|---|---:|
| 扫描文件 | 97 |
| 节点 | 3,101 |
| 边 | 22,447 |
| 未解析调用候选 | 9,632 |
| Wiki 字符 | 779,884 |

查询 `BPF_PROG_LOAD verifier` 的前列结果包含：

- `include/uapi/linux/bpf.h#BPF_PROG_LOAD:L250`
- `kernel/bpf/syscall.c#bpf_prog_load:L2634`
- `kernel/bpf/syscall.c#__sys_bpf:L5614`
- `kernel/bpf/verifier.c` 中的 verifier 相关符号

所有引用绑定提交 `adc218676eef25575469234709c2d87185ca223a`。

## 已观察限制

上游服务器在本次运行中不支持 partial-clone filter，因此使用浅克隆后再执行 sparse checkout。正则基线会把 `BPF_CALL_3` 一类宏误识别为函数；头文件或范围外定义产生大量 unresolved；函数名称唯一只能证明名称解析，不能证明编译配置下的真实调用。

9,632 个未解析候选占边总数的比例很高，证明 syntax-only 模式只能用于召回和研究导航，不能直接支撑高风险影响结论。下一精度层应加入 Tree-sitter C grammar、Kconfig/编译数据库、clang/SCIP 与 BTF 交叉验证，并重新执行同一快照的差异评测。

Linux 源码和生成的 77 万字符 Wiki 没有提交到书籍仓库；仓库只保留工具、测试 fixture、固定提交和本报告，读者可按 README 重建。
