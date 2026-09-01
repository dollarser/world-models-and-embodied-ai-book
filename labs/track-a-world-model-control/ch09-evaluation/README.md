# EXP-09-01：指标排序反转

该实验 v3 包含三个确定性反例：更低的 one-step RMSE 不保证更好的闭环动作选择；丢弃中断 rollout 后的 available-case 长时均值也可能反转系统排序；一个粗糙的单 bin ECE 会让恒定 `0.5` base-rate forecast 与按结果分离的 `0.9/0.1` forecast 同为零，而 Brier/log loss 和固定两 bin ECE 能暴露差异。它同时显式报告 action sensitivity、逐 horizon attempted/available count、coverage、预注册缺失惩罚下的固定分母均值，以及概率预测的 bin edge。

概率表只有四个作者构造的二元结果。它演示 ECE 对分箱敏感且不能单独代表 probabilistic forecast quality，不估计总体校准、真实碰撞概率、世界模型 uncertainty 或部署风险。

```bash
make ch09-smoke-local
make ch09-test-local
make ch09-smoke
```

实验不下载数据、无需 GPU，只使用 Python 标准库和 MIT 许可的程序化 fixture。缺失惩罚 2.0 只定义本反例中的失败语义，不是其他任务的推荐值；实验不运行视频模型、仿真器或真实控制系统。
