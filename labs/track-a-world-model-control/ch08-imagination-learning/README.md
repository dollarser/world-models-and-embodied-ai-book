# EXP-08-01：imagined λ-return 与 continuation smoke

解析型三步序列用于检查 λ-return、终止掩码，以及 imagined reward 偏差如何进入 critic target。

```bash
make ch08-test-local
make ch08-smoke-local
make ch08-smoke
```

实验没有训练世界模型、actor 或 critic，也不与真实环境交互。手工 target 只验证 Dreamer 风格数据接口，不能当作策略改进、样本效率或 Dreamer 复现结果。代码和 fixture 按 MIT 许可发布。
