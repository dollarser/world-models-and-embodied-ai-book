# EXP-05-01：多模态未来与概率路径 smoke

解析 fixture 对比确定性均值与条件离散分布，检查 diffusion forward process 和直线 flow path 的端点，并用条件 TV、已观察 mode recall 与观察 support 外概率质量区分条件忽略、模式坍缩和虚构 mode。三成员 range gate 再对比可拒绝的高分歧 OOD 与无法发现的共同错误。它只验证生成式预测和不确定性诊断的最小概念接口。

```bash
make ch05-test-local
make ch05-smoke-local
make ch05-smoke
```

本实验不训练 VAE、tokenizer、自回归、扩散、flow 或 ensemble 模型，不下载图像/视频，也不比较生成质量、OOD 检出率或校准。成员预测、target、OOD 标签和阈值均为手写；range 不是概率或安全保证。代码和程序化数据按仓库 MIT 许可发布。
