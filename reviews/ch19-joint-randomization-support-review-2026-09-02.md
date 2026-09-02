# 第19章联合随机化支持审查

> 日期：2026-09-02
> 范围：第19章正文、`EXP-19-01` v4、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

第19章已提醒逐参数范围不等于联合支持，但原 fixture 的 `covers()` 只检查 gain、delay 和 observation scale 的独立边界。读者仍可能把每一维 min/max 都覆盖目标误写成目标参数组合可由 joint sampler 产生。

## 修正

- aligned 与 crossed support 都使用 gain `{0.8,1.0}`、delay `{1}`、scale `{1.0,1.25}`；
- aligned 包含目标 `(0.8,1,1.25)`，crossed 只包含交叉配对 `(0.8,1,1.0)` 与 `(1.0,1,1.25)`；
- 两套 support 的逐维范围检查都通过，但目标联合点检查分别通过与拒绝；
- `EXP-19-01` 升至 v4，新增 `TAB-19-04`、`CLAIM-19-09`、`SELF-CHECK-19-06` 与4项测试。

## 验收

```bash
make ch19-test-local
make ch19-smoke-local
python3 scripts/check_results.py
make check-strict
git diff --check
```

本阶段把第19章测试从15项增至19项，全书从412项增至416项；声明增至214条，其中122条为 `result`；练习/自检增至144组。

## 剩余边界

两套 support 都只有两个手工离散点，只证明逐维边际范围不能识别这两个联合集合。它们不是连续或经验随机化分布，不估计目标附近概率质量、参数相关性、拒绝采样、训练暴露、策略鲁棒性或 Sim2Real 性能。没有运行 MuJoCo、MetaDrive、CARLA、Isaac、GPU、机器人或车辆。
