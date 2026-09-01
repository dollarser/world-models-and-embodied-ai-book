# 第11章动作指标与开源代际审查

> 审查日期：2026-09-01
> 范围：第11章正文、`EXP-11-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过；视频 checkpoint、真实数据、GPU、仿真和闭环策略仍未运行

## 1. 指标错误与修复

原 fixture 把 `unique predicted futures / action count` 命名为 action sensitivity。完全忽略动作的模型只有一个唯一未来，却得到 0.25；这与第9章“同状态预测极差”和第10章“候选动作预测差”的零点语义冲突。v2 改为预测未来的最大两两欧氏距离：action-blind 为 0，正确 action-conditioned 为 2，并保留网格单位。

仅修零点仍不够，因为敏感不代表正确。新增 `left_right_swapped` 标签置换负对照：它和正确模型的敏感度、无符号左右分离都为 2，但有符号左右效果为 -2 而非 +2，counterfactual vector RMSE 为 1.63299 而非 0。正文据此把 sensitivity、signed effect 和 oracle-relative vector error 分为三层。

## 2. 多步分母

原结果只报告三条未见序列的平均终点误差，可能遗漏中间漂移或误差抵消。v2 固定并输出 3 条序列、9 个预测转移；action-blind、swapped、conditioned 的全轨迹 RMSE 分别为 0.76830、1.33333、0，平均终点误差分别为 1.33852、2、0。该结果仍是确定性可组合规则，不估计复杂视频泛化。

## 3. 一手资料与项目角色

- DIAMOND 官方仓库提供代码、checkpoint、逐游戏/seed 结果和可玩入口，并提醒 Atari ROM 需要使用者拥有许可；MIT 代码不覆盖游戏资产。
- V-JEPA 2 官方仓库把 V-JEPA 2-AC 作为 latent action-conditioned checkpoint；它不是像素 renderer。
- Cosmos-Predict2.5 官方仓库列出 2B robot/action-cond 模型、推理和后训练文档，代码与权重分别使用 Apache-2.0 和 NVIDIA Open Model License；仓库现为有限维护并建议迁移 Cosmos 3。
- Cosmos-Drive-Dreams 提供驾驶条件合成 pipeline、权重、toolkit 和数据，但 HD map/LiDAR/box 条件生成不能自动归类为 ego-action 闭环 simulator。

这些资料只支持项目接口、资产与维护状态。本书没有下载或运行任何模型，也没有由参数量推断 24 GB 可行性。

## 4. 代码与一致性

第11章由 6 增至 12 个单元测试，全书由 197 增至 203 个。新增测试覆盖动作盲零敏感度、敏感但方向错误的负对照、counterfactual vector error、固定序列/转移分母、全轨迹误差，以及非有限状态、非法 render size、空动作序列和未知模型。实验卡升级为 fixture v2，正文、结果、manifest 与发布统计同步。
