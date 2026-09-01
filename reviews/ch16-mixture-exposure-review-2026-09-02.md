# 第16章 mixture 采样暴露审查

> 日期：2026-09-02
> 范围：第16章正文、`EXP-16-01` v3、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

第16章已定义 per-dataset mixture 权重并警告高频、长 episode 和重复采集会支配训练，但原 `EXP-16-01` 只验证跨本体动作 schema。它没有把 dataset、episode、transition 三种“均匀抽样”变成可执行对照，也没有区分配置权重与真正进入 batch/loss 的 realized exposure。

Octo 官方 commit `241fb3514b7c40957a86d869fecb7c7fc353f540` 的 [`make_interleaved_dataset`](https://github.com/octo-models/octo/blob/241fb3514b7c40957a86d869fecb7c7fc353f540/octo/data/dataset.py)接受 per-dataset `sample_weights`；`balance_weights` 会把它们乘以各数据集 `num_transitions`，随后归一化并在 frame level interleave。该实现锚点支持“采样单位和开关改变权重语义”的接口事实，但不是本书运行 Octo 或证明某种 mixture 最优。

## 修正

- 新增 `mixture_exposure_report`，强制登记每个来源的 episode 长度并输出 dataset/episode/transition 三套分母；
- 固定 short 来源1条×2步、long 来源3条×4步，总计2个来源、4条 episode、14个 transition；
- dataset-uniform 为50%/50%，episode-uniform 为25%/75%，transition-uniform 为14.2857%/85.7143%；
- `EXP-16-01` 升至 v3，新增 `TAB-16-05`、`CLAIM-16-09`、`SELF-CHECK-16-06` 与3项测试；
- 正文进一步要求记录 action/window horizon、padding/drop、过滤、`ignore_errors`、mask 后有效 token 与分布式 shard 的 realized exposure。

## 验收

```bash
make ch16-test-local
make ch16-smoke-local
make ch16-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第16章测试从12项增至15项，全书从351项增至354项；声明增至198条，其中106条为 `result`；练习/自检增至128组。

## 剩余边界

来源名、episode 数和长度都是手工计数，比例是解析期望而非有限 batch 抽样实测。fixture 没有实现窗口重叠、padding、过滤、mask、重复采样、distributed shard 或 optimizer，因此不能估计有效 token、梯度贡献、数据质量、正/负迁移或策略性能；也没有下载 Open X-Embodiment/DROID/LeRobot、运行 Octo、训练模型、使用 GPU、仿真、机器人或车辆。
