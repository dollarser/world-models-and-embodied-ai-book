# EXP-07-01：有限时域规划与价值等价 smoke

两动作、三状态的手工 MDP 用穷举候选说明短 horizon、terminal value、扰动后重规划和受限 Bellman/value-equivalence 接口；另一组五场景手工回报说明期望回报、经验下尾均值和 chance constraint 可以给出不同选择。

```bash
make ch07-test-local
make ch07-smoke-local
make ch07-smoke
```

实验没有训练世界模型、policy 或 value function，也没有实现 CEM/MCTS。穷举 2^H 与五个等权场景只用于得到可审计参考结果，不估计真实尾部风险，也不是规划算法性能。代码和 fixture 按 MIT 许可发布。
