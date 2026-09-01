# 第19章系统辨识可辨识性审查

> 审查日期：2026-09-01
> 范围：第19章正文、`EXP-19-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：修复一项会导致错误科学结论的结构混淆；通过 S 档内容、代码、一致性和教学审查

## 关键发现

旧 fixture 声称从 observation 精确恢复 gain、delay 和 scale，但其观测方程只依赖 `gain×scale`。目标 `(0.8,1,1.25)` 与替代 `(1.0,1,1.0)` 的乘积相同，对任意动作序列都产生相同 observation。旧 `min()` 仅凭 gain 排序恰好挑中目标，把 tie-break 误写成参数恢复；held-out action 也无法修复结构不可辨识。

## 修复

- calibration result 显式返回全部等价 minimizer 与 `identifiable` 状态；
- observation-only 报告两个零误差解，不再把排序首项称作恢复参数；
- 替代解在 held-out action 上 observation MAE 仍为 `0`，但 state MAE `0.1625`、terminal error `0.25`；
- 加入独立 state anchor 后，手工网格中只剩目标参数一个 minimizer，留出 state/observation gap 为零；
- trajectory metric 和 calibration 输入现在拒绝 NaN、Inf、长度错配与非法 state anchor。

## 内容核验

MuJoCo 当前官方 sysid toolbox 支持 box-constrained nonlinear least squares、finite-difference Jacobian、batched rollout、多个测量序列、measurement delay/gain/bias 与报告置信区间。本章据此补充实现入口，但明确优化器和置信区间不能替代结构可辨识性审计。域随机化的独立参数边界覆盖也不等于相关联合分布覆盖。

## 证据边界

state anchor 在 fixture 中直接可得，真实系统未必拥有；唯一解来自无噪目标恰在 12 项离散网格。没有运行 MuJoCo sysid、MetaDrive、CARLA、Isaac、MJX、RialTo、GPU、机器人或车辆，也没有证明连续参数、接触动力学或真实 Sim2Real。
