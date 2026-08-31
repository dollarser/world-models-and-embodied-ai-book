# EXP-04-01：数据契约审计

该实验对一个有效 fixture 和一个注入错误的 fixture 执行 metadata 审计，覆盖时间频率、frame index、动作范围、归一化范围和跨 split group 泄漏。

```bash
make ch04-test-local
make ch04-smoke-local
make ch04-smoke
```

实验不下载真实 LeRobot 或驾驶数据；通过 smoke 只证明审计规则能够识别已注入问题。
