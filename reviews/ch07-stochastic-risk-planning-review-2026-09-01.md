# 第7章随机传播与风险目标审查

> 审查日期：2026-09-01  
> 基线：`76a77eb` 之后的工作树  
> 范围：第7章正文、`EXP-07-01`、实验卡、fixture、测试、结果与跨章接口

## 1. 问题与修正

原章能解释 horizon、terminal value、MPC/CEM、tree search 和 value equivalence，但只用一句话提及不确定性惩罚。读者从第5章的多未来与第6章 latent stochasticity 进入规划时，仍缺三个关键接口：随机变量从哪里来、ensemble/particle 身份如何跨时间传播、均值与尾部风险为何会改变选择。

本次新增 7.8 节，区分当前 belief、aleatoric dynamics 与 epistemic model uncertainty；用 PETS 一手论文锚定 probabilistic ensemble/trajectory sampling，用 PMLR 论文锚定随机动力系统中的 CVaR 优化。正文不采用论文 benchmark 数字，也没有声称本书复现这些算法。

## 2. 可执行反例

`EXP-07-01` v2 增加两个动作、每个五个等权 hand-authored return：

- `steady = [0.6, 0.6, 0.6, 0.6, 0.6]`；
- `risky = [1.5, 1.5, 1.5, 1.5, -2.0]`。

固定结果为：均值分别 0.6/0.8，最差 20% 均值分别 0.6/-2.0，失败概率分别 0/0.2。因而均值选择 risky，而下尾目标和 `P(failure)≤0.1` 都选择 steady。新增 `CLAIM-07-07` 只声明这个固定排序反例，不估计真实尾部概率，不证明概率校准或安全。

新增 3 个测试覆盖排序反转、chance constraint 与 NaN/布尔/空输入拒绝；第7章由 7 个增至 10 个测试，全书由 256 个增至 259 个。

## 3. 跨章一致性

- 第5章：多未来必须保留分布，不能先压成均值；
- 第6章：prior/ensemble 不确定性进入规划前需声明采样身份；
- 第9章：场景生成、阈值 split 与分母进入评测协议；
- 第17章：有限粒子和共同模型偏差仍可被优化器利用；
- 第21章：统计风险目标不能替代独立执行网关。

## 4. 保留边界

fixture 只有五个等权手工场景，没有训练 probabilistic ensemble，没有概率校准、CEM/MCTS、仿真、GPU、机器人或车辆。经验下尾均值是教学算术，不是置信上界、功能安全指标或道路风险估计。

## 5. 验证

提交前要求以下命令全部返回 0：

```bash
make ch07-test-local
make ch07-smoke
make check
make docs-preview-check
git diff --check
```
