# EXP-07-01：有限时域规划与价值等价 smoke

两动作、三状态的手工 MDP 用穷举候选说明短 horizon、terminal value、扰动后重规划和受限 Bellman/value-equivalence 接口。扰动实验同时输出旧版不等动作预算负对照、固定两动作槽的 reward-only 对照，以及把环境 reward 与 terminal-value contribution 分开的固定预算目标。另一组五场景手工回报说明期望回报、经验下尾均值和 chance constraint 可以给出不同选择；`αN` 非整数时，正式下尾均值按分位点边界质量计权，并把最差 `ceil(αN)` 个样本均值保留为显式粗略对照。

```bash
make ch07-test-local
make ch07-smoke-local
make ch07-smoke
```

实验没有训练世界模型、policy 或 value function，也没有实现 CEM/MCTS。穷举 2^H、单个固定扰动与五个等权场景只用于得到可审计参考结果；terminal value 是手工冻结的 bootstrap，不是观测到的环境回报。尾部离散化对照不估计 population CVaR、置信区间或真实尾部风险，也不是规划算法性能。代码和 fixture 按 MIT 许可发布。
