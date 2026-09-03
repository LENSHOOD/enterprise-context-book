import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const base = process.env.DOCS_BASE || '/'

export default withMermaid(defineConfig({
  lang: 'zh-CN',
  title: '企业上下文',
  description: '从知识库到智能体认知基础设施',
  base,
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: [
    /^knowledge:\/\//,
    /^code:\/\//,
    /^runtime:\/\//,
    /^memory:\/\//
  ],
  head: [
    ['meta', { name: 'theme-color', content: '#315b4c' }],
    ['meta', { name: 'author', content: 'xuhai.zhang' }]
  ],
  themeConfig: {
    logo: '/logo.svg',
    siteTitle: '企业上下文',
    nav: [
      { text: '正文', link: '/part-1/chapter-01' },
      { text: '企业案例', link: '/part-4/chapter-14' },
      { text: 'Linux 案例', link: '/part-5/chapter-18' },
      { text: '全内核番外', link: '/extras/full-linux-kernel' },
      { text: '研究索引', link: '/research-notes' },
      { text: '附录', link: '/appendices' }
    ],
    sidebar: [
      {
        text: '第一部分 认识企业上下文',
        collapsed: false,
        items: [
          { text: '1. 为什么智能体需要企业上下文', link: '/part-1/chapter-01' },
          { text: '2. 知识管理的历史演进', link: '/part-1/chapter-02' },
          { text: '3. 上下文的类型与边界', link: '/part-1/chapter-03' }
        ]
      },
      {
        text: '第二部分 核心知识能力',
        collapsed: false,
        items: [
          { text: '4. RAG：访问外部证据', link: '/part-2/chapter-04' },
          { text: '5. 混合检索', link: '/part-2/chapter-05' },
          { text: '6. 层级知识', link: '/part-2/chapter-06' },
          { text: '7. Wiki：编译知识', link: '/part-2/chapter-07' },
          { text: '8. 知识建模、本体与图谱', link: '/part-2/chapter-08' },
          { text: '9. 智能体记忆', link: '/part-2/chapter-09' }
        ]
      },
      {
        text: '第三部分 平台架构与治理',
        collapsed: false,
        items: [
          { text: '10. 上下文基础设施', link: '/part-3/chapter-10' },
          { text: '11. 对象、版本与时间', link: '/part-3/chapter-11' },
          { text: '12. 权限、安全与行动', link: '/part-3/chapter-12' },
          { text: '13. 评测与运营', link: '/part-3/chapter-13' }
        ]
      },
      {
        text: '第四部分 Northstar 实践',
        collapsed: false,
        items: [
          { text: '14. 成品导览与构建路线', link: '/part-4/chapter-14' },
          { text: '15. 从来源到可信检索', link: '/part-4/chapter-15' },
          { text: '16. 从企业语言到可导航知识', link: '/part-4/chapter-16' },
          { text: '17. 从上下文到经验证行动', link: '/part-4/chapter-17' }
        ]
      },
      {
        text: '第五部分 大型代码库实践',
        collapsed: false,
        items: [
          { text: '18. Linux eBPF 知识库', link: '/part-5/chapter-18' },
          { text: '番外：完整 Linux 内核', link: '/extras/full-linux-kernel' },
          { text: '附录', link: '/appendices' },
          { text: '研究索引', link: '/research-notes' },
          { text: '许可与引用', link: '/license' }
        ]
      }
    ],
    search: { provider: 'local' },
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一章', next: '下一章' },
    lastUpdated: { text: '最后更新' },
    footer: {
      message: '书稿 CC BY-NC-SA 4.0 · 配套代码 Apache-2.0',
      copyright: 'Copyright © 2026 xuhai.zhang'
    }
  },
  markdown: {
    lineNumbers: true,
    math: true
  }
}))
