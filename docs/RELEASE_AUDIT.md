# v1.0.0-rc.2 发布审计

> 文档类别：候选版本发布门与证据状态。

审计日期：2026-08-28。发布裁决以 `reviews/run_manifest.json` 的 `verdict` 为唯一事实源；本表只记录证据状态。

| 要求 | 当前证据 | 验证方式 | 状态 |
|---|---|---|---|
| 8—12 万字可发布初稿 | 当前 56,348 个中文正文字符，距下限 23,652 | `python3 scripts/wordcount.py --minimum 80000` | 未通过 |
| 论证与引用 | 就近引用存在；集中参考文献表与声明级复核尚未完成 | 人工来源审计，尚无完整记录 | 未通过 |
| Northstar 案例 | 最小纵向切片、24 条教学题集、数据契约和受控动作闭环 | `python3 -m unittest discover -s tests -v` | 通过（教学范围） |
| Linux eBPF 案例 | CLI、fixture 与 syntax-only 测试 | 案例目录运行 `unittest discover` 和 `python3 -m linux_kb ingest --help` | 通过（syntax-only） |
| 完整 Linux 番外 | 保存 Markdown 报告；缺少本次全仓运行的机器可读原始摘要 | 人工复核报告，无法在 CI 重跑全仓 | 未验证 |
| VitePress 与 Mermaid | 构建接入 Mermaid 转换和内部死链检查 | `npm run docs:build` 后检索 `language-mermaid` | 通过 |
| 浏览器 QA | 旧 QA 早于本轮结构与 Mermaid 修改 | 桌面与 375px 人工复核 | 未验证 |
| GitHub Pages | 测试通过后允许构建与 RC 预览；独立 `release_gate` 继续执行 8 万字发布门 | 远端 Actions 运行记录 | 未验证 |
| 版本控制接入 | 位于父级 Git 工作树，但书稿尚未纳入索引或独立公开仓库 | `git ls-files`、提交哈希与发布 tag | 未通过 |
| 许可与维护 | 双许可证、贡献、安全和版本材料存在 | 核对根目录法律文本 | 通过 |

## 已知边界

- Linux 基线是 `syntax-only`，真实 v6.12 运行报告记录 9,632 个未解析候选；它用于召回和研究导航，不声称编译器精度。
- Northstar 使用离线同义词 Jaccard 代理而非向量检索；数据库、REST/MCP、持久任务和真实工具网关均未交付。
- 完整 npm 开发依赖审计包含 Vite 开发服务器已知问题；生产静态依赖审计为零，站点不部署开发服务器。
- 项目目录目前位于父级 Git 工作树中但尚未纳入索引；是否拆成独立公开仓库、首次提交与推送属于发布动作，不在本轮修订授权范围内。

## 待执行发布动作

版本控制接入需要由发布者在两条路径中选择一条：将本书纳入父仓库索引并在发布提交上打 tag；或拆出独立公开仓库，再配置 GitHub Pages。面向个人公开发布时，独立仓库的权限、Issue、勘误和发布历史更清晰，因此是默认建议；本轮不代替发布者执行建仓、提交、推送或远端配置。

执行前应确认 `node_modules/`、`book/.vitepress/dist/` 与各级 `__pycache__/` 不进入索引，`package-lock.json` 进入索引；执行后记录仓库 URL、发布 commit、tag、Actions 运行和 Pages 地址，才能关闭 `version_control_integration` 与 `remote_pages_verification`。
