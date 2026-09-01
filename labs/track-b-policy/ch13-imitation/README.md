# EXP-13-01：误差累积与动作分块协议 smoke

该实验用 Python 标准库构造四个确定性反例：同为 `0.02` RMSE/MAE 的持续同号与正负交替动作误差，在 20 步单位增益标量积分器中的最终状态误差分别为 `0.40` 与 `0`；两个手写策略在唯一专家支持点上的 action MSE 都为0，但同受 `0.25` 扰动后，6步最终绝对状态分别为 `0.00390625` 与 `2.84765625`；固定 prediction horizon=8 后，execution horizon 越长，policy query 越少但扰动后的陈旧动作等待越久；同一 temporal ensemble 可在稳态预测中降抖，也会在真实 target 突变时滞后。

它不训练 BC 或 ACT；新增反馈策略也是手写标量诊断，因而不代表 learned policy 或真实机器人性能。其用途是检查评测代码是否同时报告 expert-support 范围、扰动 rollout、teacher-forced 动作误差、误差的时间结构与积分状态后果、prediction/execution horizon、丢弃后缀、重规划次数、反应延迟和时间集成的两面性。

```bash
make ch13-test-local
make ch13-smoke-local
make ch13-smoke
```

数据为仓库内程序化 fixture，下载量 0，按仓库 MIT 许可发布。
