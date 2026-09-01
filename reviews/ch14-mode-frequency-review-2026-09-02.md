# 第14章模式覆盖与频率诊断审查

> 日期：2026-09-02
> 范围：第14章正文、`EXP-14-01` v3、fixture、测试、结果、实验卡、manifest、PRD 与快速演进官方来源

## 发现

原章已经把动作有效性、模式覆盖、闭环结果和安全筛选拆开，并在评测矩阵中提醒“样本频率与真实条件频率”需要单独评估。但 `EXP-14-01` 只报告 `covered_mode_count`：只要少数样本触及稀有模式，覆盖数就达到最大，无法区分等权目标下的5:5与9:1生成频率。因而正文的重要教学边界尚缺可执行反例。

快速来源复核同时确认：LeRobot 当前 `main` 仍是 `128d3324e3202ce1fca1340fb8d7941edecce9d3`，其 DiffusionConfig 继续拆分 observation horizon、prediction horizon、execution steps 和 inference steps；openpi 当前 `main` 为 `215abfb217dbac7d5f1273282331b9b1866c0479`，README 仍说明 π0 为 flow-based、公开 π0.5 训练/推理仅支持 flow-matching head，并保留推理/LoRA/full fine-tuning 的上游内存估算。正文语义无需改变，但 openpi 读者链接从浮动仓库首页升级为该完整 commit 的 README。

## 修正

- 新增 `mode_frequency_report`，只在所有样本都通过模式有效性门时，计算相对已知目标模式频率的经验 total variation；
- 固定等权目标与两个10样本集合：5:5和9:1均为100%有效、覆盖2个模式，经验 TV 分别为0和0.4；
- 将该量明确标为有限手工样本上的描述性诊断，不把它称作总体 calibration、显著性或 mode-collapse 发生率；
- `EXP-14-01` 升至 v3，新增 `TAB-14-05`、`CLAIM-14-09`、`SELF-CHECK-14-06` 与3项测试；
- openpi 方法与资源说明锁定到 `215abfb217dbac7d5f1273282331b9b1866c0479`。

## 验收

```bash
make ch14-test-local
make ch14-smoke-local
make ch14-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第14章测试从14项增至17项，全书从342项增至345项；声明增至195条，其中103条为 `result`；练习/自检增至125组。

## 剩余边界

目标分布由作者直接设为等权，两个候选集合也不是模型随机输出；经验 TV 没有置信区间，且模式标签、条件充分性和目标频率都不存在估计误差。真实生成策略还需独立 test 条件、重复随机 seed、proper score、闭环 episode、在线选择器和失败分母。当前没有下载 Push-T/LIBERO/openpi 资产，没有训练 diffusion/flow/VLA，也没有验证 GPU、显存、墙钟时延、机器人、车辆或安全性。
