# 第17章世界模型效用与 support gate 审查

> 审查日期：2026-09-01
> 范围：第17章正文、`EXP-17-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过 S 档内容、代码、一致性和教学审查；不升级 learned world model、仿真或 GPU 状态

## 发现与修复

旧版 fixture 证明平均 `8/9` 转移一致仍可能选择碰撞捷径，但正文建议的 coverage/OOD 拒绝没有可执行对照；Spearman 实现也用无并列秩公式并以名字打破 tie，在策略分数并列时会给出错误统计含义。

本轮新增显式 state-action support：训练支持只覆盖每个位置的 `advance/wait`，高回报 `shortcut` 属于 support 外查询。无门禁时模型选择 `phantom_shortcut`、真实 regret 为 `1.85`；门禁后拒绝该策略，在两个覆盖内策略中选择 `safe_route`，fixture regret 为 `0`。同时把 Spearman 改为平均秩上的 Pearson 相关；常量排名返回“未定义”错误，而不是伪造零相关。

## 内容核验

- 五类用途改为非互斥数据流角色，同一系统可同时承担表征、生成、交互、规划和安全检查；
- 真实性锚点按锁定规则、独立物理仿真、既有日志和真实系统分层，仿真不能改名为 real-world result；
- WorldGym 代理评测拆为 action/schema 注入、world-model rollout、自动/VLM outcome scorer 三段误差；
- TD-MPC2 当前 episodic task 支持需显式 `episodic=true`，termination/bootstrap 语义纳入复现合同；
- Cosmos 3 的 policy、inverse dynamics、forward dynamics action modes 分开，只有 forward dynamics 对候选动作做未来预测。

## 固定结果

- 第17章 10 个单元测试通过；
- 平均转移一致率 `8/9`，模型所选首转移仍错误；
- 三策略 Spearman `-0.5`，最大 return gap `2.0`，无门禁 exploitation regret `1.85`；
- support gate 拒绝 1/1 support 外策略，选择 `safe_route`，真实终点为 goal，fixture regret `0`。

## 证据边界

support 是手工 oracle 集合，不是 learned density、ensemble 或 conformal estimator；它不能发现 support 内模型错误、共享偏差或真实系统风险。没有运行 V-JEPA 2-AC、DreamerV3、TD-MPC2、WorldGym、Cosmos、仿真器、GPU、机器人或车辆。
