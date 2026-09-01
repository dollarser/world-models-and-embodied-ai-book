# EXP-02-01：四轴系统卡与 state-aliasing 反例

该实验用 8 张结构化系统卡检查“表示、动态、条件、用途”四个轴，并强制记录每个系统现有证据不能支持的能力。v3 继续用 `supported / unsupported / scope_dependent` 分开时间转移、候选动作干预、学习式动作转移和“策略输出但无独立转移”，并加入当前观测相同、历史线索不同、最优动作相反的 state-aliasing 反例。它是分类与状态充分性契约 smoke，不是性能 benchmark、POMDP solver 或现实项目比例调查。

```bash
make ch02-test-local
make ch02-smoke-local
make ch02-smoke
```

fixture 为 MIT 许可的原创结构化摘要；被引用论文、项目和文档仍遵循各自许可证。
