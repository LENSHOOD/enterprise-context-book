# Linux v6.12 全仓知识建模实验报告

## 2026-09-17 复核重跑

为复核书稿结论，本次在 macOS 区分大小写的临时 APFS 卷中，用同一提交 `adc218676eef25575469234709c2d87185ca223a` 重新运行 targeted 和全仓流程。全仓模式实际处理 `tracked_paths=86,680`、`files=64,862`，生成 `706,269` 个函数候选、`136,596` 个类型候选、`907,727` 个节点和 `3,848,019` 条边；其中 `1,259,312` 条调用按全局唯一名称解析，`1,745,842` 条保留为候选，数据库约 `2.83 GB`，扫描与写入约 `94.533` 秒，总耗时约 `121.799` 秒。六组查询均退出成功。

这组数据与下文 2026-08-23 的历史运行不同。差异来自代码过滤、对象 ID、运行环境和统计口径变化；它们不能互相覆盖，也不能被当成性能基准。targeted 的递归范围本次为 107 个文件、3,076 个节点、12,743 条边和 6,570 个未解析候选。审计日志和完整命令保存在本地复核目录，源码与数据库没有进入仓库。

本次还增加了输入契约检查：不存在的仓库或 Git ref 会拒绝，Git 模式从请求的 ref 读取树内容，类型 ID 带路径和行号，重复节点插入返回原稳定 ID。`syntax-only` 仍不代表编译级调用图。

运行日期：2026-08-23

## 快照与环境

- 上游：Linux kernel.org
- tag：`v6.12`
- commit：`adc218676eef25575469234709c2d87185ca223a`
- 跟踪路径：86,680
- 展开工作树：约 1.8 GB
- 模式：`sqlite-syntax-only`
- 数据库：SQLite + FTS5，按源码路径分子系统

## 两次运行

第一次直接放大 eBPF 内存版思路：类型正则把使用位置当成定义，全局调用解析对每个候选执行相关计数。约 8 分钟后仍停在关系解析，临时数据库及 WAL 已超过 3 GB。该运行被终止，证明“对象先全部生成、之后逐边解析”不适合全仓。

优化版只抽取带函数体的类型定义，逐文件提交到 SQLite，先建立 `name → target_count/min(id)` 聚合表，再批量解析调用。结果：

| 指标 | 结果 |
|---|---:|
| 全部耗时 | 175.809 秒 |
| 扫描与写入 | 137.970 秒 |
| 纳入文件/文档 | 64,882 |
| 函数候选 | 1,352,851 |
| 类型定义候选 | 127,055 |
| 总节点 | 1,544,788 |
| 总边 | 5,601,741 |
| 全局名称唯一调用 | 1,676,138 |
| 模糊或缺失调用候选 | 2,436,142 |
| SQLite 文件 | 3,881,082,880 bytes（`du` 约 3.6 GB） |

“函数候选”显著高于合理的编译级函数数量，说明正则仍会把宏形态和复杂声明误判为函数。全局名称唯一也只是一种名称解析，不是特定 Kconfig/架构下的编译器调用关系。

## 最大子系统

| 子系统投影 | 文件 | 函数候选 | 类型候选 |
|---|---:|---:|---:|
| `drivers/gpu` | 6,776 | 123,699 | 10,623 |
| `include` | 6,204 | 21,802 | 22,275 |
| `drivers/net` | 5,637 | 221,778 | 26,743 |
| `tools` | 4,156 | 57,290 | 5,146 |
| `drivers/media` | 2,500 | 61,438 | 5,534 |
| `sound/soc` | 1,596 | 34,980 | 2,328 |
| `arch/x86` | 1,186 | 22,184 | 1,393 |
| `kernel` | 532 | 30,059 | 982 |
| `fs/xfs` | 321 | 8,580 | 462 |

这不是单一目录树的最终本体，只是便于路由和容量分片的路径投影。后续应叠加 MAINTAINERS、Kconfig、Makefile/Kbuild 与运行架构视图。

## 查询效果

以下耗时来自同一台本地机器、已建立的 SQLite 数据库，不是正式基准：

| 查询 | 子系统 | CLI 耗时 | 首屏观察 |
|---|---|---:|---|
| `schedule wake_up_new_task pick_next_task_fair` | `kernel` | 0.10s | 两个目标符号排前二；出现 `if` 伪符号 |
| `ext4 journal write inode` | `fs/ext4` | 0.15s | 命中 inode 与 journal 入口；出现三个 `if` 伪符号 |
| `tcp congestion control retransmit` | `net/ipv4` | 0.10s | 前列集中在 `tcp_input.c`、`tcp_cong.c` |
| `drm atomic commit` | `drivers/gpu` | 0.33s | 命中 atomic commit 与 helper 路径 |
| `BPF_PROG_LOAD bpf_check verifier` | `kernel` | 0.07s | 命中 verifier、syscall 和 prog load；出现 `if` |
| `rcu grace period synchronize_rcu` | `kernel` | 0.08s | 命中 synchronize 与 tasks/tree；出现 `if` |

实验后已在摄取和查询层过滤 C 控制关键字。上述原始结果不改写，以保留发现问题的证据。

## 结论

1. 全仓词法索引与一级子系统路由在单机 SQLite 上可行，精确符号和领域词查询可在亚秒级返回。
2. 真正瓶颈不是 BM25，而是代码对象身份与关系精度。正则覆盖率高，但会制造大量伪节点和模糊边。
3. 将源码片段同时存入对象表与 FTS 使数据库达到 3.6 GB；正式架构应把源码放在 Git/ArtifactFS，只索引符号、摘要和定位。
4. 路径分区能限制搜索空间，却不能表达配置、维护者、构建目标和跨子系统调用，需要多视图图谱。
5. Wiki 不应为 154 万节点逐一生成。应从子系统、构建目标和高中心性模块开始，按查询热度与变更增量编译。

## 复现

```bash
python3 -m linux_kb ingest-full \
  --repo /path/to/linux --ref v6.12 \
  --database generated/linux-v6.12.db
python3 -m linux_kb report-full --database generated/linux-v6.12.db
python3 -m linux_kb query-full 'drm atomic commit' \
  --database generated/linux-v6.12.db --subsystem drivers/gpu
```

数据库、Linux 源码和生成结果未提交到书籍仓库；仓库保留实现、fixture 测试、固定提交和本报告。
