# EXP-04-01：数据契约审计

该实验对一个有效 fixture 和一个注入错误的 fixture 执行 metadata 审计，覆盖时间频率、frame index、动作范围、自然终止/外部截断、显式缺帧 mask、多传感器时间偏差、归一化范围和跨 split group 泄漏。

```bash
make ch04-test-local
make ch04-smoke-local
make ch04-smoke
```

实验不下载真实 LeRobot 或驾驶数据；通过 smoke 只证明审计规则能够识别已注入问题。`valid=false, timestamp=null` 是允许的显式传感器缺失；缺少整个传感器记录不会被当作同一件事静默接受。
