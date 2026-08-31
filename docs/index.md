# 世界模型与具身智能

> 从表征、预测到行动

这不是一份模型排行榜，而是一条从计算机视觉走向闭环智能的学习路径：观测如何成为状态，状态如何支持预测，预测如何支持决策，决策又如何在环境反馈中接受检验。

## 本书面向谁

本书默认读者熟悉 CNN、ViT/Transformer 或至少一种视觉任务，能够阅读 Python/PyTorch 代码；不要求预先学过强化学习、机器人学、控制或 3D 视觉。

## 当前可读内容

- [第2章：世界模型到底是什么](part-01-loop/ch02-what-is-a-world-model.md)
- [第4章：数据、基线与实验协议](part-01-loop/ch04-data-and-protocols.md)
- [第6章：World Models 与循环状态空间模型](part-02-world-models/ch06-rssm.md)
- [第9章：世界模型如何评测与失败](part-02-world-models/ch09-evaluation.md)
- [编写状态](status.md)

## 当前限制

当前版本已进入全书分批编写阶段。第6章和第9章已有 CPU smoke；第2章和第4章的轻量实验仍为 planned。现有实验用于验证数据流、状态更新和评测协议，不是 Dreamer、PlaNet 或大型 benchmark 的完整复现，也没有验证 24 GB GPU 训练成本。
