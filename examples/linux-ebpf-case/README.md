# Linux eBPF 代码知识库案例

该案例实现第 18 章的离线 `syntax-only` 基线：扫描固定 Linux 源码快照，抽取文件、C 函数、类型、BPF 命令和候选调用，生成对象图、BM25 查询、层级 Wiki 与未解析关系报告。它明确不把正则解析结果称为编译器精确调用图。

## 使用内置 fixture

```bash
cd examples/linux-ebpf-case
python3 -m linux_kb ingest \
  --repo fixtures/linux --ref fixture-v1 --fixture --output generated \
  --scope 'kernel/bpf/*.c' \
  --scope 'include/uapi/linux/bpf.h' \
  --scope 'Documentation/bpf/*.rst'
python3 -m linux_kb query 'BPF_PROG_LOAD verifier' --snapshot generated
python3 -m linux_kb build-wiki --snapshot generated
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## 使用 Linux 上游源码

```bash
git clone --filter=blob:none https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
git -C linux checkout v6.12
python3 -m linux_kb ingest --repo linux --ref v6.12 --output generated-v6.12
```

输出包括 `manifest.json`、`nodes.json`、`edges.json`、`unresolved.json` 和 `wiki.md`。完整工程可将提取器替换为 Tree-sitter、clang/SCIP 和 BTF 适配器；Manifest 的 `mode` 必须随精度升级，调用边仍保留证据等级。内置 fixture 没有 Git 历史，必须显式使用 `--fixture`；真实 Git 仓库则必须解析 `--ref`，不会回退为 fixture 身份。

Git 仓库输入会从 `--ref` 指定的提交读取文件树，并把该提交写入每条引用；不存在的仓库或 ref 会直接失败。无 Git 的内置 fixture 才使用 `fixture:<ref>` 身份。类型节点的 ID 包含路径和行号，避免不同文件中的同名类型被合并。

本书发布候选已对真实 Linux `v6.12` 执行上述流程。固定提交、规模和误差水位参见 `INTEGRATION_REPORT.md`。

## 完整内核 SQLite 模式

全仓模式逐文件写入 SQLite，使用 FTS5 建立词法索引，并在第二阶段解析全局唯一函数名。它避免将全仓节点和边同时放入内存：

```bash
python3 -m linux_kb ingest-full \
  --repo /path/to/linux --ref v6.12 --database generated/linux-v6.12.db
python3 -m linux_kb report-full --database generated/linux-v6.12.db
python3 -m linux_kb query-full 'schedule task tick' \
  --database generated/linux-v6.12.db --subsystem kernel
```

`CALLS_NAME_RESOLVED` 仍然只表示全仓名称唯一，不代表编译器证明。完整结果和架构分析见书中番外。
