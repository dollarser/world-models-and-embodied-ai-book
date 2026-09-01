# 第2章三态能力蕴含审查

> 审查日期：2026-09-01
> 范围：第2章正文、`EXP-02-01` v2、system card fixture、校验器、测试、结果、实验卡与 manifest
> 结论：系统名称、时间预测、候选动作干预、学习动态和直接策略输出已拆成三态证据；未把教学卡片计数写成领域统计

## 1. 发现的问题

旧四轴卡能区分 VLA、视频预测、学习模型和仿真器，但关键能力仍藏在自然语言字段中。校验器只强制三个特例，无法阻止“能输出动作所以有世界转移”“能预测视频所以支持反事实”或“接受控制所以动态是学习得到”等错误蕴含。正文还写成“3 个测试”，与实际 4 个测试不一致。

## 2. 一手资料核对

- V-JEPA 2 官方仓库把无动作视频表征与 V-JEPA 2-AC 动作条件 predictor 作为不同组件发布；同一项目名称不能替代组件级分类；
- OpenPI 官方仓库将 π₀、π₀-FAST 和 π₀.₅列为 VLA，并公开 action generation 实现；该事实不自动提供独立环境 transition；
- DreamerV3 官方仓库明确由动作条件 world model 产生 imagined trajectories，再训练 actor-critic；
- MuZero 论文明确学习供规划使用、预测 reward/value/policy 的可迭代模型，不要求像素重建。

对应一手来源：

- <https://github.com/facebookresearch/vjepa2>
- <https://github.com/Physical-Intelligence/openpi>
- <https://github.com/danijar/dreamerv3>
- <https://www.nature.com/articles/s41586-020-03051-4>

## 3. 代码与教学修复

- fixture 升为 v2，每张卡新增 `claim_status`，只允许 `supported / unsupported / scope_dependent`；
- 四项声明分别是时间/转移证据、候选动作干预、学习式动作条件转移，以及无独立转移的策略；
- `learned_action_conditioned_transition=supported` 必须同时满足 `learned_dynamics=true` 与 `action_conditioning=true`；
- VLA 动作输出不能被改写为独立转移，数字孪生 archetype 必须保留 scope-dependent；
- 校验器新增 fixture 版本、审查日期、HTTPS 来源、非空四轴、唯一 ID、唯一证据限制及封闭三态集合检查；
- 固定八卡得到 6 张转移证据、5 张动作干预、3 张学习式动作转移、1 张 scope-dependent 与 1 张无独立转移的策略。

## 4. 边界与验收

第2章由 4 增至 10 个单元测试，全书由 184 增至 190 个。`supported` 只表示锁定卡片证据支持；`unsupported` 是“不允许由当前证据发布”，不是对未来版本或全局能力的否定。八张 archetype 的计数不是样本统计，不能估计项目比例、性能或研究趋势。

阶段门禁包括 22 章 Docker smoke、22 组结果精确比对、4 个 Schema、18 个契约测试、22 张实验卡、3 张 benchmark card、严格文档构建和本地站点检查。
