# EXP-22-01：综合项目包审计 smoke

审计两个手工项目包 fixture：完整驾驶项目为 0 issue，并校验 train/selection/eval 在 group、原始来源、精确内容指纹和预登记近重复簇四个维度互斥，连同 5 个带 SHA-256 的 artifact binding、2 个失败注入、冻结独立评测、可追溯 safety gateway，以及 input、method、independent evaluation、deployment/safety gate、evidence package 五段 trace；故意无效包产生 23 个具名 issue。

```bash
make ch22-test-local
make ch22-smoke-local
make ch22-smoke
```

审计器会对内存中的固定文本 payload 重算摘要，但不遍历真实项目目录、不运行复现命令，也不读取媒体或发现未登记近重复，因此不证明科学正确性、数据独立性、许可、隐私或安全。代码和 fixture 按 MIT 许可发布。
