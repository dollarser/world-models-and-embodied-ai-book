# 第18章重采样历史可辨识性审查

> 日期：2026-09-02
> 范围：第18章正文、`EXP-18-01` v4、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

第18章 v3 已分别报告 dynamic rejection 的 attempted、rejected 与 used 分母，但仍只固定一条尝试流。若训练记录只保留 optimizer 最终使用的 batch，即使 used group、rollout 数和非零难度分布完全相同，也无法判断此前是否发生拒绝、额外 rollout 或 coverage 缺失。

## 修正

- clean 流直接尝试两个 mixed medium group，得到6条 attempted、0条 rejected、6条 used rollout；
- rejection-heavy 流先拒绝全成功 easy 与全失败 hard，再使用相同两个 medium group，得到12条 attempted、6条 rejected、6条 used rollout；
- 两条流的 used group/rollout 数与非零 used 难度分布相同，但 attempted rollout 比值为2，隐藏额外尝试数为6；
- `EXP-18-01` 升至 v4，新增 `TAB-18-06`、`CLAIM-18-11`、`SELF-CHECK-18-07` 与4项测试。

## 验收

```bash
make ch18-test-local
make ch18-smoke-local
python3 scripts/check_results.py
git diff --check
```

本阶段把第18章测试从14项增至18项，全书从408项增至412项；声明增至213条，其中121条为 `result`；练习/自检增至143组。

## 剩余边界

两条流、group 顺序、reward 和难度标签均为手工确定性 fixture。2倍 attempted rollout 只证明 used-batch 摘要不能识别这两条历史，不是长期期望重采样成本，也不估计真实接受概率、并行 worker 利用率、梯度偏差、收敛或策略性能。没有运行 VLA、RIPT-VLA、LIBERO、仿真、GPU、机器人或车辆。
