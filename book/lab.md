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

“模拟角色”用于观察权限与责任分工，允许同一读者扮演不同角色，不能代替登录认证。队列和经营数据是虚构 fixture；模拟时钟只在点击“推进61秒”时前进。C0—C7 运行固定流程，下面的 C8、C9 增加资源建设与上下文调查助手。默认脚本演示不调用模型；选择真实模型模式后，建议来自配置的模型接口，业务数据仍是模拟。

<NorthstarLab />

## C8：辅助建设和维护资源

用 product 角色登记默认原文，建立建设任务，生成建议并核对候选。审核发布后，到上面的 C1 搜索“限流窗口”，到 C3 查看模型，再到 C4 查看关系和 Wiki。选择原来源并保存新版本，可继续观察重新生成、审核和发布的过程。详细讲解见[第16章](./part-4/chapter-16.md#_16-3-4-在-c8-中从新原文构建资源)。

<ContextAssist kind="resource" />

## C9：逐步调查并交付上下文

以 SRE 身份提出退款资料问题，确认任务建议后逐步取证。再用经营负责人提出“H2 销售为什么比 H1 差”，观察任务确认与指标契约确认各自起什么作用。记录可以刷新后继续。详细讲解见[第17章](./part-4/chapter-17.md#_17-2-5-在-c9-中让助手逐步准备上下文)。

<ContextAssist kind="query" />

## 工作台怎样承载实验

工作台是运行示例的工具：Vue 页面收集输入，`lab_server.py` 接收同源 HTTP 请求，`workbench.py` 调用 Python 核心并保存练习进展。书中第14—17章讲资源建设、查询和任务处理；下面的实现细节供需要修改工作台的读者查阅。

<details>
<summary>展开实验空间的保存、恢复与并发处理</summary>

`Workspace` 保留任务条件、事件、上下文快照、政策修订和模拟运行状态。`WorkspaceStore.call()` 将一次普通请求中的读取、检查、修改与保存放在 SQLite 事务中；操作报错时不提交。数据库默认位于 `.northstar-lab/workspaces.sqlite3`。Cookie 选择当前空间，新建空间切换到另一份练习数据。

`Workspace.context()` 根据所选工作线传入核心查询参数，在返回包外补上任务条件和工作事件，再保留快照。真正的查询计划、工具调用和公共组装位于 `context_flow.py`；网页不另做一套查询计算。核心 `TaskMemory` 保存动作事件，工作台还保存业务笔记、复核和快照，两者分别保留各自记录。

修改政策或发布资源时，`Workspace._build()` 在私有数据副本中重新编译和校验。成功后才保存新状态，仓库原始样例不被改写。当前实现按整份空间保存 JSON，并保守地将旧任务标为需重新取证。

模型调用由 `WorkspaceStore.model_step()` 协调。等待模型时释放数据库事务，返回后比较空间是否变化，再提交建议和工具结果。并发冲突会拒绝旧建议，但已经发出的模型请求仍可能计费。模型调用尚未完成时重启服务，也可能需要重新调用。

空间绑定 Python 源码标识，修改代码后重启需要新建空间。SQLite 事务只保护本地模拟状态，不涵盖外部退款 API；接入真实业务时，需要第十章讨论的独立恢复与幂等机制。动作令牌保存在本地状态中而不返回页面，生产凭据还需专门保护。

</details>

## 接入真实模型

C8、C9 共用一个只返回 JSON 建议的模型接口。它接受 Chat Completions 兼容协议：请求包含 `model`、`messages`、`response_format: {"type":"json_object"}` 和 `max_tokens`，响应读取 `choices[0].message.content`。模型服务需要支持这些字段；不支持时会显示错误，不自动改变模式。

在启动本地服务的终端设置以下变量，地址使用你已获准使用的服务端点。这里只设置模型配置，不将密钥写入仓库、网页或实验结果：

```bash
export NORTHSTAR_MODEL_URL='https://your-model-service.example/v1/chat/completions'
export NORTHSTAR_MODEL='your-model-name'
# 服务要求认证时，从本地受控环境注入 NORTHSTAR_MODEL_KEY。
npm run lab
```

本机模型服务可使用 `http://127.0.0.1:端口/v1/chat/completions`；其他地址须使用 HTTPS。浏览器不能替换端点，接口拒绝跳转。页面选择“真实模型”，再建立新记录。模型网络读写超时设为45秒，页面最多等候60秒；网络超时不是整个调用的总截止时间，页面停止等待也不等于服务端已经取消，请先恢复记录再决定是否重试。每条记录最多接受八次尝试。预算按请求大小和步骤限制，不是精确计费上限；生产服务还需总截止时间、并发和费用控制。

真实模型会接收当前角色可见的材料、目录和必要的调查记录。请先使用随书的虚构资料确认行为，再依据企业的数据使用约定接入真实内容。网络失败、无效 JSON、越权工具或不符合约定的候选都会留下错误记录。

无密钥时，可以在仓库根目录运行两条脚本流程：

```bash
python3 examples/enterprise-case/src/assistant_demo.py
python3 -m unittest discover -s examples/enterprise-case/tests -p 'test_intelligence.py' -v
```

配置模型后运行 `python3 examples/enterprise-case/src/assistant_demo.py --mode http`，会实际请求资源候选和任务理解，但不会替读者审核发布。该命令使用临时空间，退出后删除；要继续确认、取证和保存记录，请使用工作台。脚本演示和接口测试证明流程与边界，真实模型在企业问题上的效果还需另行评测。

可以回到[第14章系统设计](./part-4/chapter-14.md)理解资源、平台和任务的关系。W2 与 Linux 是独立练习，尚未接入本工作台。
