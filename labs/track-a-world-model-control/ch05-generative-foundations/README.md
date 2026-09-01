# EXP-05-01：多模态未来与概率路径 smoke

解析 fixture 对比确定性均值与条件离散分布，检查 diffusion forward process 和直线 flow path 的端点，并用条件 TV、已观察 mode recall 与观察 support 外概率质量区分条件忽略、模式坍缩和虚构 mode。它只验证生成式预测的最小概念接口。

```bash
make ch05-test-local
make ch05-smoke-local
make ch05-smoke
```

本实验不训练 VAE、tokenizer、自回归、扩散或 flow 模型，不下载图像/视频，也不比较生成质量。代码和程序化数据按仓库 MIT 许可发布。
