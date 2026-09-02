# EXP-18-01：离线轨迹奖励重加权 smoke

四条两阶段标量轨迹用于检查 episode reward 重加权如何移动监督 target，同时降低 effective sample size 与 recovery 样本权重。实验还比较逐阶段 min/max 与最近完整轨迹门禁，计算全成功、全失败和混合 reward group 的未归一化 leave-one-out advantage，并用固定 easy/medium/hard context 组区分 dynamic rejection 的 attempted、rejected 与 used 分布。v4 再比较两个 used batch 摘要相同的确定性流：clean 历史尝试6条 rollout，rejection-heavy 历史尝试12条。

```bash
make ch18-test-local
make ch18-smoke-local
make ch18-smoke
```

实验没有训练 VLA/RL policy、reward model 或 world model，也没有运行 LIBERO。成功子集均值、joint-support 距离、阈值、难度标签和尝试顺序都是手工参考，不是真实任务 oracle、密度、可达性、期望重采样成本或 RIPT-VLA 采样率；target 更接近它不能当作闭环策略改进。代码和 fixture 按 MIT 许可发布。
