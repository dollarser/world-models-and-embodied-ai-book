# 第18章联合支持与相对优势退化审查

> 审查日期：2026-09-01
> 范围：第18章正文、`EXP-18-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过 S 档内容、代码、一致性和教学审查；不升级 VLA/RL、world model、仿真或 GPU 状态

## 发现与修复

旧 fixture 只用每个 phase 的观测 min/max 判断 support。这会接受把不同轨迹的合法边缘拼成从未见过的组合；正文还讨论了 RLOO 全成功/全失败组退化，却没有可执行证据。

本轮新增最近完整轨迹 MAE 门禁。`(0.9,0.8)` 的两个标量各自在 marginal 范围内，但到最近完整轨迹的 MAE 为 `0.35`，高于手工阈值 `0.1`，因此 marginal 接受、joint 拒绝。另新增未归一化 leave-one-out baseline：三条全成功或全失败 reward 的 advantage 都为零，混合 `(1,0,0)` 为 `(1,-0.5,-0.5)`。

## 内容核验

- 区分 trajectory、transition、task-group 和 token 级 ESS/归一化分母；
- dynamic sampling 可去掉零相对信号组，但必须报告 attempted、discarded、resampled 与 used groups，且会改变任务难度分布；
- World-Gymnast 的 partial-credit rubric、WMPO 的 policy/world/reward checkpoint 均作为独立版本资产登记；
- WMPO 官方整包约 `364 GiB` checkpoint 加 `530 GiB` 数据，默认禁止整包下载；
- SimWAM 当前 isolated attention mask 使 action token 不读取 future-video token，部署丢弃视频分支，因此不具备在线 imagined-future 比较接口；
- WAM survey taxonomy 仍在演化，能力判断回到动作条件、递归、future-token 可见性和 reward/termination 接口。

## 固定结果

- 第18章 11 个单元测试通过；
- reward weighting 仍保持 reference MAE `0.30→0.15`、ESS `4.0→3.2`、recovery mass `0.50→0.25`；
- 未见组合 `(0.9,0.8)` marginal gate 接受、joint gate 拒绝，最近轨迹 MAE `0.35`；
- 全成功和全失败组均无非零 LOO signal，混合组有非零 signal。

## 证据边界

最近邻距离、阈值和成功参考均为手工 oracle，不是状态条件行为密度、动力学可达性或安全证明。LOO 只计算 reward-minus-other-samples，没有 policy ratio、归一化、clipping、KL、optimizer 或重采样成本。没有运行 RIPT-VLA、World-Gymnast、WMPO、SimWAM、VLA、world model、LIBERO、仿真器、GPU、机器人或车辆。
