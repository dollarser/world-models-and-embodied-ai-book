# EXP-09-01：指标排序反转

该实验包含两个确定性反例：更低的 one-step RMSE 不保证更好的闭环动作选择；丢弃中断 rollout 后的 available-case 长时均值也可能反转系统排序。它同时显式报告 action sensitivity、逐 horizon attempted/available count、coverage 和预注册缺失惩罚下的固定分母均值。

```bash
make ch09-smoke-local
make ch09-test-local
make ch09-smoke
```

实验不下载数据、无需 GPU，只使用 Python 标准库和 MIT 许可的程序化 fixture。缺失惩罚 2.0 只定义本反例中的失败语义，不是其他任务的推荐值；实验不运行视频模型、仿真器或真实控制系统。
