# 企业上下文：从知识库到智能体认知基础设施

本仓库包含书稿、Northstar Commerce 企业上下文案例和 Linux eBPF 代码知识库案例。

当前公开版本是 `v1.0.0-rc.2` 发布候选，不代表正式版已经通过全部发布门。正文包含 18 章及完整 Linux 内核番外，位于 `book/`；可运行案例位于 `examples/`。已知缺口与验收状态见[发布审计](docs/RELEASE_AUDIT.md)。

- [在线阅读](https://lenshood.github.io/enterprise-context-book/)
- [项目文档](docs/README.md)
- [同行评审记录](reviews/README.md)

## 阅读与构建

```bash
npm install
npm run docs:dev
```

生产构建使用 `npm ci && npm run docs:build`。推送到 `main` 后，GitHub Actions 工作流会构建并部署 Pages；仓库 Settings 中需将 Pages Source 设为 GitHub Actions。

## 本地验证

```bash
npm test
npm run docs:build
```

Northstar 演示混合检索、ACL、图、Wiki、记忆和 Context Package；Linux 案例演示固定源码快照、C 结构抽取、关系图、查询、Wiki 与误差报告。两者均提供不依赖商业 API 的本地路径。

Linux 案例还提供全仓 SQLite/FTS5 模式，并已在真实 `v6.12` 的 86,680 个跟踪路径上运行。详见 `book/extras/full-linux-kernel.md` 与 `examples/linux-ebpf-case/FULL_KERNEL_REPORT.md`。

## 仓库结构

```text
book/       VitePress 书稿、附录与研究索引
docs/       写作宪章、案例规格、目录和发布审计
examples/   Northstar 与 Linux eBPF 可运行案例
reviews/    历史评审、处置记录与证据清单
scripts/    确定性检查脚本
```

## 许可

书稿、图表和非代码文档采用 CC BY-NC-SA 4.0；配套代码与构建配置采用 Apache License 2.0。详见 `LICENSE` 与 `LICENSE-CODE`。
