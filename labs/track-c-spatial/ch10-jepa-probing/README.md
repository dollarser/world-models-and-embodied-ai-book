# EXP-10-01：表征偏移、动作接口与时间顺序诊断 smoke

该实验构造三个手工表征：保留高能量纹理的 `appearance`、保留任务变量的 `task_predictive` 和完全坍塌的 `collapsed`。probe 只在训练集拟合，再分别评测未参与拟合的同分布集和纹理相关性反转集，因此：

- `appearance` 的重建误差更低，ID probe 为 100%，但 shifted probe 降为 0%；
- `task_predictive` 无法重建纹理，却保留任务变量；
- `collapsed` 用作 probe 实现的负对照。

第二个解析诊断让 `action_blind` 与 `action_conditioned` 都精确暴露当前状态，但只有后者使用候选动作预测下一状态。它检查“状态可读”与“动作反事实转移正确”不是同一个声明，并为第11章的动作条件模型建立接口门禁。

第三个解析诊断构造成对的三帧标量序列：相同中间状态分别向正、负方向演化。`middle_frame` 与 `ordered_delta` 都能零误差读出中间状态，但前者在平衡方向标签上只有 50% 准确率且对时间反转不敏感，后者为 100% 且反转敏感度为 4。它只验证“当前状态可读”不蕴含“保留时间箭头”。

```bash
make ch10-test-local
make ch10-smoke-local
make ch10-smoke
```

该 fixture 不加载 V-JEPA、I-JEPA 或任何官方 checkpoint，不代表视频理解、模型性能、因果理解或规划成功率。时间序列是八条手写三标量轨迹，不是视频 benchmark。代码和程序化数据按仓库 MIT 许可发布。
