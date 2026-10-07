---
title: Northstar 工作台与章节实验
outline: false
---

# Northstar 工作台与章节实验

在这里检查企业资源、阅读真实代码，再把一次任务从条件确认推进到证据复核或结果验证。工作台和第15—17章的实验使用同一套组件、接口和 Python 核心。

公开书站提供源码与构建时示例。要实际执行，请先安装 Git、Node.js 22 和 Python 3.10 或更新版本，确认终端能运行 `git`、`npm` 和 `python3`，然后克隆[配套仓库](https://github.com/LENSHOOD/enterprise-context-book)并启动：

```bash
git clone https://github.com/LENSHOOD/enterprise-context-book.git
cd enterprise-context-book
npm ci
npm run lab
```

随后打开 [本地工作台](http://127.0.0.1:8765/lab)。该命令先构建书站，再启动只监听本机的 Python 服务；本地第14—17章也能直接运行嵌入实验。无需模型密钥或额外数据库服务。

如果已经克隆过仓库，请先更新代码，再在仓库根目录执行后两条命令。服务运行期间保持终端打开；按 `Ctrl+C` 可以停止，下次运行 `npm run lab:serve` 即可继续使用已经构建的版本。修改或更新源码后，应停止旧服务，再用 `npm run lab` 重新构建并启动。

若8765端口已被占用，完成构建后运行 `npm run lab:serve -- --port 8766`，按终端显示的地址访问。不要为运行实验停止其他应用。若之前使用 `DOCS_BASE` 构建过站点，本地请先取消该变量，再执行 `npm run lab`，确保书页从根路径加载。

第一次点击“新建实验空间”。数据自动保存在 `.northstar-lab/workspaces.sqlite3`，刷新页面或重启同一版本服务后可继续。一个浏览器的页面共享当前空间；不同浏览器 Cookie 使用不同空间。新建空间会切换当前空间，旧记录仍保留在数据库，本版尚未提供旧空间选择器。不要将这个教学服务暴露到公网。

“模拟角色”用于观察权限与责任分工，允许同一读者扮演不同角色，不能代替登录认证。队列和经营数据是虚构 fixture；模拟时钟只在点击“推进61秒”时前进。实际运行 Python 不代表连接了真实业务系统，也不包含自动规划的模型智能体。

<NorthstarLab />

下一步可以回到[第14章系统设计](./part-4/chapter-14.md)，理解资源、平台和任务的关系；或者按 C0—C7 顺序在这里完成实验。W2 与 Linux 是独立练习，尚未接入本工作台。
