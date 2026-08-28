# 安全说明

发布站点是 GitHub Pages 上的纯静态文件，不包含服务端、身份系统或真实企业数据。`npm run docs:dev` 和 `npm run docs:preview` 只应绑定本机回环地址，不应暴露到不可信网络。

本发布候选固定使用 VitePress 1.6.4（以 `package.json` 为准）。2026-08-27 执行 `npm audit --omit=dev` 为零；完整开发依赖审计仍报告 Vite 开发服务器链路中的已知问题，当前 VitePress 版本没有兼容修复。CI 对受信任的仓库内容运行测试并构建纯静态站点，只上传 `book/.vitepress/dist`，不部署开发服务器或执行站点访客输入。依赖升级后必须重新执行审计、站点构建和浏览器 QA。

案例数据全部为虚构 fixture。请勿向 Issue、测试数据或日志提交真实企业文档、源码秘密、访问令牌和个人数据。安全问题可通过 GitHub Security Advisory 私下报告。
