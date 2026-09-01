# 第2章 state aliasing 与任务相关状态审查

> 日期：2026-09-01
> 范围：第2章、`EXP-02-01` v3、`CLAIM-02-06`、`TAB-02-03`
> 结论：通过当前 S 档的内容、代码、一致性与教学审查

## 缺口与修订目标

原第2章能够按表示、推进、条件和用途分类系统，也能阻止从“动作输出”推断“环境转移”。但“任务相关状态”只靠文字问题说明，实验没有验证两个需要不同动作的历史能否被同一表示错误合并。该缺口会让读者误以为低维、可预测或 action-conditioned representation 自动等于充分 state。

本轮增加 state-aliasing 反例，要求证据链明确区分：

1. 当前 observation 是否相同；
2. 历史是否包含可消歧线索；
3. 两个 context 的最优动作是否不同；
4. current-only policy 的最优共享动作仍保留多少 regret；
5. history-aware oracle 关闭的 gap 是否只属于固定 fixture。

## 固定模型与结果

两个 context 等权，当前 observation 都是 `occluded-corridor`：

| context | history cue | advance | hold | optimal |
| --- | --- | ---: | ---: | --- |
| clear | corridor seen clear | 1.0 | 0.0 | advance |
| blocked | obstacle seen before occlusion | -1.0 | 0.2 | hold |

- current-only：选择 `hold`，mean return `0.1`，mean regret `0.5`；
- history-aware oracle：mean return `0.6`，mean regret `0.0`；
- history value gap：`0.5`。

这里的 return 无单位，context probability 是人为固定的均匀分布。若改动权重、return 或动作集，数字会改变；fixture 不估计碰撞概率、真实 reward 或 population performance。

## 一手来源与蕴含边界

- [DeepMDP](https://proceedings.mlr.press/v97/gelada19a.html)把 reward 和 next-latent distribution prediction 与 MDP/bisimulation 表示条件连接；正文只据此说明任务相关表示不能只看外观重建，不声称本 fixture 满足其理论假设。
- [The Value Equivalence Principle](https://arxiv.org/abs/2011.03506)把等价性定义在选定 policy/function 集合的 Bellman updates 上；正文据此强调“可忽略什么”依赖用途，不把一次决策 regret 当作 value-equivalence 证明。
- [MuZero](https://www.nature.com/articles/s41586-020-03051-4)预测 reward、value 与 policy 以服务 planning；正文把它作为价值相关路线，不把其论文结果当本书复现。
- [POBAX 论文](https://arxiv.org/abs/2508.00046)提出 memory-improvable gap 作为部分可观测 benchmark 信号；[源码锁定到 `a5e1d62d14e4efe783885b9d4f19cffa2a568eec`](https://github.com/taodav/pobax/tree/a5e1d62d14e4efe783885b9d4f19cffa2a568eec)。当前只做来源/接口审计，没有安装 JAX 或运行训练。

## 代码、测试与限制

- `analyze_state_aliasing` 明确采用等权 context、相同行为集合和每 context 唯一最优动作；
- 输入合同拒绝重复 history cue、不一致 action set、context 或共享策略最优动作 tie、bool、非数值与非有限 return；
- 第2章测试由 10 个增加到 14 个；
- smoke 和中央结果保存 context 最优动作、共享动作、mean return、regret 与 weighting；
- 实验卡、manifest、PRD、正文声明和图表登记同步为 fixture v3。

没有 learned encoder、RNN/Transformer、belief estimator、长期 transition、随机观测、训练分布、POMDP solver、GPU、仿真器、机器人或车辆。history-aware 数字来自 oracle，不证明模型能够学习、保持或泛化记忆。

阶段门禁已通过：`make smoke-all` 覆盖全书 270 个章节测试，`make check` 覆盖 52 项严格规格测试并精确比对 22 组 smoke 结果，`make docs-preview-check` 验证 28 个 HTML、22 章、23 张可访问 Mermaid 图和 1073 个内部目标；`git diff --check` 无格式错误。
