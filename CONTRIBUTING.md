# 贡献指南

本项目接受勘误、引用修正、案例测试和内容建议。事实性修改请优先引用论文、规范、官方文档或版本化源码。

## 本地检查

```bash
npm ci
npm run docs:build
python3 -m unittest discover -s examples/enterprise-case/tests -v
cd examples/linux-ebpf-case
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

正文贡献按 CC BY-NC-SA 4.0 发布，代码贡献按 Apache-2.0 发布。请勿提交真实企业数据、访问令牌、个人敏感信息或 Linux 内核源码副本。
