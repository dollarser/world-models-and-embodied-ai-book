# EXP-22-01：综合项目包审计 smoke

审计两个手工项目包 fixture：完整驾驶项目为 0 issue，并校验互斥 train/selection/eval route、5 个带 SHA-256 的 artifact binding、2 个失败注入、冻结独立评测、可追溯 safety gateway，以及 input、method、independent evaluation、deployment/safety gate、evidence package 五段 trace；故意无效包产生 20 个具名 issue。

```bash
make ch22-test-local
make ch22-smoke-local
make ch22-smoke
```

审计器会对内存中的固定文本 payload 重算摘要，但不遍历真实项目目录、不运行复现命令，也不证明科学正确性、许可、隐私或安全。代码和 fixture 按 MIT 许可发布。
