# EXP-13-01：误差累积与动作分块协议 smoke

该实验用 Python 标准库构造三个确定性反例：每步 `0.02` 的动作偏差在 20 步闭环中积分为 `0.40` 状态误差；固定 prediction horizon=8 后，execution horizon 越长，policy query 越少但扰动后的陈旧动作等待越久；同一 temporal ensemble 可在稳态预测中降抖，也会在真实 target 突变时滞后。

它不训练 BC 或 ACT，不代表真实机器人成功率。其用途是检查评测代码是否同时报告 teacher-forced 动作误差、闭环状态误差、prediction/execution horizon、丢弃后缀、重规划次数、反应延迟和时间集成的两面性。

```bash
make ch13-test-local
make ch13-smoke-local
make ch13-smoke
```

数据为仓库内程序化 fixture，下载量 0，按仓库 MIT 许可发布。
