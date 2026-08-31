# EXP-22-01：综合项目包审计 smoke

审计两个手工项目 metadata 包：完整驾驶项目为 0 issue；故意缺失问题、许可、隔离、结果、失败、资源和安全字段的项目产生 15 个具名 issue。

```bash
make ch22-test-local
make ch22-smoke-local
make ch22-smoke
```

审计器只检查 metadata 合同，不读取真实 artifact 内容，也不证明科学正确性、许可、隐私或安全。代码和 fixture 按 MIT 许可发布。
