# EXP-16-01：跨本体动作适配 smoke

两个二维动作张量拥有相同 shape，但 `delta_x` 分别使用 controller delta unit 与厘米，夹爪正负含义也相反。实验比较直接混合 raw action 与先转换到 `(delta_x_m, gripper_open_fraction)` 规范空间再混合。

```bash
make ch16-test-local
make ch16-smoke-local
make ch16-smoke
```

它不训练策略，也不证明跨本体正迁移；只验证 schema adapter、round-trip 与缺失 metadata 拒绝。代码和程序化 fixture 按仓库 MIT 许可发布。
