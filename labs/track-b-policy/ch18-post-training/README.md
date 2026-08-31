# EXP-18-01：离线轨迹奖励重加权 smoke

四条两阶段标量轨迹用于检查 episode reward 重加权如何移动监督 target，同时降低 effective sample size 与 recovery 样本权重。

```bash
make ch18-test-local
make ch18-smoke-local
make ch18-smoke
```

实验没有训练 VLA/RL policy、reward model 或 world model，也没有运行 LIBERO。成功子集均值是手工参考，不是真实任务 oracle；target 更接近它不能当作闭环策略改进。代码和 fixture 按 MIT 许可发布。
