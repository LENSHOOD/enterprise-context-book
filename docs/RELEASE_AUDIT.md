# v1.0.0-rc.3 发布审计

> 文档类别：候选版本发布门与证据状态。

审计日期：2026-08-30。发布裁决以 `reviews/run_manifest.json` 的 `verdict` 为唯一事实源；本表只记录证据状态。

| 要求 | 当前证据 | 验证方式 | 状态 |
|---|---|---|---|
| 8—12 万字可发布初稿 | 当前 60,250 个中文正文字符，距下限 19,750 | `python3 scripts/wordcount.py --minimum 80000` | 未通过 |
| 论证与引用 | 就近引用存在；集中参考文献表与声明级复核尚未完成 | 人工来源审计，尚无完整记录 | 未通过 |
| Northstar 案例 | 最小纵向切片、24 条教学题集、数据契约、受控动作闭环和企业架构一致性检测 | `python3 -m unittest discover -s tests -v`（39 项） | 通过（教学范围） |
| Linux eBPF 案例 | CLI、fixture 与 syntax-only 测试 | 案例目录运行 `unittest discover`（10 项）和 `python3 -m linux_kb ingest --help` | 通过（syntax-only） |
| 完整 Linux 番外 | 保存 Markdown 报告；缺少本次全仓运行的机器可读原始摘要 | 人工复核报告，无法在 CI 重跑全仓 | 未验证 |
| VitePress 与 Mermaid | 构建接入 Mermaid 转换和内部死链检查 | `npm run docs:build` 后检索 `language-mermaid` | 通过 |
| 浏览器 QA | 线上首页与第 8 章已在 1280×720、375×812 复核；无横向溢出或破图，Mermaid 已转为 SVG，搜索“本体”命中预期结果，控制台无错误 | 浏览器人工复核 | 通过 |
| GitHub Pages | `main` 推送自动执行测试、构建与 Pages 部署；独立 `release_gate` 继续执行正式版 8 万字门 | `docs.yml` 工作流；本次 RC 的远端运行由发布流程核验 | 已配置，发布后核验 |
| 版本控制接入 | 已建立独立公开仓库，首个发布提交为 `509056ef04428fe9510b1af71a164c6d520aedea` | 仓库、提交、tag 与 Release | 通过 |
| 许可与维护 | 双许可证、贡献、安全和版本材料存在 | 核对根目录法律文本 | 通过 |

## 已知边界

- Linux 基线是 `syntax-only`，真实 v6.12 运行报告记录 9,632 个未解析候选；它用于召回和研究导航，不声称编译器精度。
- Northstar 使用离线同义词 Jaccard 代理而非向量检索；数据库、REST/MCP、持久任务和真实工具网关均未交付。
- 完整 npm 开发依赖审计包含 Vite 开发服务器已知问题；生产静态依赖审计为零，站点不部署开发服务器。
- 本项目使用嵌套的独立 Git 根目录，未将父级文档仓库的任何文件纳入公开历史；`node_modules/`、VitePress 构建产物和 Python 缓存均被忽略。

## 发布记录

- 公开仓库：<https://github.com/LENSHOOD/enterprise-context-book>
- 在线阅读：<https://lenshood.github.io/enterprise-context-book/>
- 首次部署提交：`509056ef04428fe9510b1af71a164c6d520aedea`
- 首次 Pages 流水线：<https://github.com/LENSHOOD/enterprise-context-book/actions/runs/33179598875>
- 发布版本：`v1.0.0-rc.3`（预发布）

该版本已公开，但 `verdict` 仍为 `not-cleared`：它是可阅读、可运行的 RC 预览，不等同于已通过篇幅、集中参考文献和完整 Linux 全仓机器证据门的正式 `v1.0.0`。
