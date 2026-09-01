# EXP-17-01：世界模型决策效用 smoke

三个固定策略同时在“真实规则”和一个有单点盲区的“学习世界模型”中 rollout。学习模型在 9 个单步转移中答对 8 个，却把会碰撞的 `shortcut` 预测成成功到达，因而选择错误策略并造成排序反转。对照门禁把训练支持集外的 `shortcut` 拒绝后，只在覆盖内策略中选择。

```bash
make ch17-test-local
make ch17-smoke-local
make ch17-smoke
```

该实验只验证 simulator gap、平均秩 Spearman、support gate 和 policy exploitation 的评测接口，不训练世界模型，也不估计 learned OOD detector、真实机器人或自动驾驶中的效应大小。手工 support gate 不能发现覆盖内错误。代码与程序化 fixture 按仓库 MIT 许可发布。
