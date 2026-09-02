# EXP-09-01：指标排序反转

该实验 v4 包含四组确定性反例：更低的 one-step RMSE 不保证更好的闭环动作选择；丢弃中断 rollout 后的 available-case 长时均值也可能反转系统排序；粗糙单 bin ECE 会让恒定 base-rate 与 informative forecast 同为零；另两组 forecast 的 mean Brier 同为0.16，但 threshold accuracy 为1/0.75、最大单例 log loss 为0.510826/1.203973。它同时显式报告 action sensitivity、逐 horizon attempted/available count、coverage、预注册缺失惩罚下的固定分母均值、bin edge 与逐 outcome probability loss。

概率表只有四个作者构造的二元结果。它演示 ECE 对分箱敏感、mean proper score 仍可能隐藏误差集中，不能估计总体校准、概率损失尾部、真实碰撞概率、世界模型 uncertainty 或部署风险。

```bash
make ch09-smoke-local
make ch09-test-local
make ch09-smoke
```

实验不下载数据、无需 GPU，只使用 Python 标准库和 MIT 许可的程序化 fixture。缺失惩罚 2.0 只定义本反例中的失败语义，不是其他任务的推荐值；实验不运行视频模型、仿真器或真实控制系统。
