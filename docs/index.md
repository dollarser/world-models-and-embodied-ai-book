# 世界模型与具身智能

> 从表征、预测到行动

这不是一份模型排行榜，而是一条从计算机视觉走向闭环智能的学习路径：观测如何成为状态，状态如何支持预测，预测如何支持决策，决策又如何在环境反馈中接受检验。

## 本书面向谁

本书默认读者熟悉 CNN、ViT/Transformer 或至少一种视觉任务，能够阅读 Python/PyTorch 代码；不要求预先学过强化学习、机器人学、控制或 3D 视觉。

## 当前可读内容

- [第1章：从“看见”到“行动”](part-01-loop/ch01-from-seeing-to-acting.md)
- [第2章：世界模型到底是什么](part-01-loop/ch02-what-is-a-world-model.md)
- [第3章：具身任务的最小机器人学与决策基础](part-01-loop/ch03-minimal-robotics-and-decision.md)
- [第4章：数据、基线与实验协议](part-01-loop/ch04-data-and-protocols.md)
- [第5章：预测模型的生成式基础](part-02-world-models/ch05-generative-foundations.md)
- [第6章：World Models 与循环状态空间模型](part-02-world-models/ch06-rssm.md)
- [第7章：用模型做规划——从 PlaNet 到价值等价模型](part-02-world-models/ch07-model-based-planning.md)
- [第8章：在想象中学习——Dreamer 系列](part-02-world-models/ch08-imagination-learning.md)
- [第9章：世界模型如何评测与失败](part-02-world-models/ch09-evaluation.md)
- [第10章：非生成式预测表示——从 I-JEPA 到 V-JEPA 2.x](part-03-representations/ch10-jepa-representations.md)
- [第11章：动作条件视频世界模型](part-03-representations/ch11-action-conditioned-video.md)
- [第12章：可行动的空间表征](part-03-representations/ch12-actionable-space.md)
- [第13章：模仿学习、误差累积与动作分块](part-04-policies/ch13-imitation-and-action-chunks.md)
- [第14章：生成动作——Diffusion Policy 与 Flow Matching](part-04-policies/ch14-generative-actions.md)
- [第15章：VLA 的架构模式](part-04-policies/ch15-vla-architecture-patterns.md)
- [第16章：数据规模化、跨本体迁移与高效适配](part-04-policies/ch16-data-scaling-and-adaptation.md)
- [第17章：世界模型帮助策略的五种方式](part-05-fusion/ch17-world-model-policy-utility.md)
- [第18章：VLA 后训练、长时序与 World-Action Models](part-05-fusion/ch18-vla-post-training-and-wam.md)
- [第19章：物理仿真、Real2Sim 与 Sim2Real](part-06-systems/ch19-physical-simulation-and-sim2real.md)
- [第20章：具身评测——从成功率到部署证据](part-06-systems/ch20-embodied-evaluation.md)
- [第21章：部署、实时性与安全边界](part-06-systems/ch21-deployment-realtime-and-safety.md)
- [第22章：端到端综合项目——一个可审计的具身研究闭环](part-07-capstone/ch22-auditable-capstone.md)
- [读者术语表](glossary.md)
- [研究雷达：怎样阅读快速演进的世界模型研究](research-radar.md)
- [编写状态](status.md)

## 当前限制

当前版本已接入 22 章正文。第1–9章的 50 道练习已有可折叠自检要点；第10–22章仍按批次补齐，当前不提供全书答案承诺。

每章均有零下载或微型 CPU smoke；这些实验只验证定义、数据流、target、状态更新、几何、空间状态、动作合同和评测协议，不是 Dreamer、ACT、VLA、occupancy 网络、仿真 benchmark 或真实机器人/车辆的完整复现，也没有验证待办实验的 24 GB GPU 训练成本。
