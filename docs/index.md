# 世界模型与具身智能

> 从表征、预测到行动

这不是一份模型排行榜，而是一条从计算机视觉走向闭环智能的学习路径：观测如何成为状态，状态如何支持预测，预测如何支持决策，决策又如何在环境反馈中接受检验。

## 本书面向谁

本书默认读者熟悉 CNN、ViT/Transformer 或至少一种视觉任务，能够阅读 Python/PyTorch 代码；不要求预先学过强化学习、机器人学、控制或 3D 视觉。

## 当前可读内容

- [第2章：世界模型到底是什么](part-01-loop/ch02-what-is-a-world-model.md)
- [第3章：具身任务的最小机器人学与决策基础](part-01-loop/ch03-minimal-robotics-and-decision.md)
- [第4章：数据、基线与实验协议](part-01-loop/ch04-data-and-protocols.md)
- [第6章：World Models 与循环状态空间模型](part-02-world-models/ch06-rssm.md)
- [第9章：世界模型如何评测与失败](part-02-world-models/ch09-evaluation.md)
- [第10章：非生成式预测表示——从 I-JEPA 到 V-JEPA 2.x](part-03-representations/ch10-jepa-representations.md)
- [第11章：动作条件视频世界模型](part-03-representations/ch11-action-conditioned-video.md)
- [第12章：可行动的空间表征](part-03-representations/ch12-actionable-space.md)
- [第13章：模仿学习、误差累积与动作分块](part-04-policies/ch13-imitation-and-action-chunks.md)
- [第20章：具身评测——从成功率到部署证据](part-06-systems/ch20-embodied-evaluation.md)
- [编写状态](status.md)

## 当前限制

当前版本已进入全书分批编写阶段。已接入正文的章节均有零下载或微型 CPU smoke；这些实验只验证定义、数据流、状态更新、几何、空间状态和评测协议，不是 Dreamer、ACT、occupancy 网络、仿真 benchmark 或真实机器人/车辆的完整复现，也没有验证待办实验的 24 GB GPU 训练成本。
