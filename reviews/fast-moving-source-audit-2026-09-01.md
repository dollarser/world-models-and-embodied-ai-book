# 快速演进来源与版本接口审查：第9–11、15、18–21章

> 审查日期：2026-09-01  
> 审查基线：`d787fb3` 之后的工作树  
> 范围：近期 benchmark、JEPA、动作条件视频、VLA/WAM、仿真、评测与部署来源  
> 结论：修正 2 处证据成熟度抬高，确认 1 处同行评审状态，补入 2 个高价值版本接口；未运行模型、数据、GPU、仿真或硬件

## 1. 发表状态复核

| 来源 | 一手元数据证据 | 修订后标记 | 结论 |
| --- | --- | --- | --- |
| [WorldArena 2.0](https://arxiv.org/abs/2605.17912) | arXiv 仅显示 2026-05-18 的 v1，未列接收场次 | `[A/O,R0–R1]` | 论文与官方资产分开标注，原 `[P/O]` 过高 |
| [KineBench](https://arxiv.org/abs/2607.19876) | arXiv Comments 明确写明已接收 ECCV 2026 | `[P,R0]` | `P` 有一手依据；本书未运行，仍为 `R0` |
| [RoboArena](https://arxiv.org/abs/2506.18123) | arXiv v2 未列接收场次 | `[A,R0]` | 论文不能因有官方项目页而写成 `[O]` |

规范同步增加硬边界：arXiv 提交、arXiv DOI、作者项目页和“已投稿”都不等于同行评审；`P` 需要明确的已接收/发表一手元数据。

## 2. 版本接口补强

### Cosmos 2.5→3

[Cosmos-Predict2.5 官方仓库](https://github.com/nvidia-cosmos/cosmos-predict2.5)已转有限维护并指向 [Cosmos 3](https://github.com/NVIDIA/cosmos)。Cosmos 3 官方仓库把 Generator 的输入输出扩展到 text、vision、sound 与 action，同时明确列出 temporal inconsistency、action-state consistency、3D 结构和物理合理性限制。第11章因此新增代际行与 `CLAIM-11-10`：统一 action 接口是可审计能力，不是 simulator fidelity、安全或控制有效性的替代证据。

### GR00T N1.7 的四个 horizon

[GR00T N1.7 README](https://github.com/NVIDIA/Isaac-GR00T) 与[模型主配置](https://github.com/NVIDIA/Isaac-GR00T/blob/main/gr00t/configs/model/gr00t_n1d7.py)给出最大 `action_horizon=40` 和最大 action dimension 132；[官方数据配置](https://github.com/NVIDIA/Isaac-GR00T/blob/main/getting_started/data_config.md)示例仍常用 16 步 `delta_indices`，并要求改变窗口后重算逐步统计；rollout 又使用 `execution-horizon` 表示本次消费前缀。第15章新增 `TAB-15-04` 与 `CLAIM-15-09`，强制分别记录模型容量、数据窗口、checkpoint 实际输出和执行窗口。

## 3. 保持不变的来源边界

- V-JEPA 2/2.1 仍按预印本 + 官方代码 `[A/O,R1]`，80M–2B checkpoint 与 dense/deep-supervision 描述有官方仓库支持；
- 第18章 2025–2026 WAM/post-training 工作继续保守标为 `[A,R0]` 或 `[A/O,R1]`，没有把上游结果改成本书实测；
- MuJoCo/MJX/sysid、LeRobot sync/RTC/async、ROS 2 和 Autoware 的接口描述仍由官方文档支持 `[O,R1]`；这些资产存在不证明目标硬件实时性、仿真有效性或安全完成。

## 4. 一致性与后续风险

本轮新增 2 条非 `result` 声明，不改变 75 条 S 档实验结果。全书现在有 164 条声明；新增图表也暴露旧门禁只能检查“登记项是否出现”，因此已将全部 `FIG/TAB` 的正文—manifest 双向相等和章节归属加入 `BLOCK` 检查。

仍需后续处理：为所有快速演进来源锁定 commit 或版本快照；逐条复核供应商页面的能力措辞；对图表做应用内浏览器的人工视觉/可访问性检查；目标 GPU、仿真和真实系统验证继续保持可选且未完成。
