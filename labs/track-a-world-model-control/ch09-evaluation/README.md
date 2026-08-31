# EXP-09-01：指标排序反转

该实验用两个确定性预测器说明：更低的 one-step RMSE 不保证更好的闭环动作选择。它不是神经世界模型训练，也不对应任何论文 benchmark 分数。

```bash
make ch09-smoke-local
make ch09-test-local
make ch09-smoke
```

实验不下载数据、无需 GPU，只使用 Python 标准库和 MIT 许可的程序化 fixture。
