# 第14章生成动作预算与筛选审查

> 审查日期：2026-09-01
> 范围：第14章正文、`EXP-14-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过；learned diffusion/flow、Push-T/LIBERO、GPU、真实时延和碰撞器仍未运行

## 1. 候选数漏算与修复

原 fixture 的预算函数只比较单样本 solver 步数和可用调用数。正文同时生成 10 个候选，却把“4 步小于 8 次调用”直接判为可行，未说明候选是串行还是 batched。v2 显式输入 solver 步数、候选数、batch 容量和 forward 预算，并同时输出 sample-model evaluation 与顺序 forward：10 候选、4 步逐个执行为 40 个 forward，单 batch 为 4 个；16 步即使单 batch 也为 16 个。

这些仍是抽象计数。真实 batch P95、显存、调度和端到端 deadline 必须在目标硬件测量，不能从 forward 数推断。

## 2. 模式有效不等于场景安全

新增独立手工门禁，把左模式设为当前场景阻塞区。正负模式各 5 个时，10 个候选都接近演示模式，但只有 5 个通过安全门；两个候选都位于阻塞模式时，系统使用确定性 fallback，而不是无限重采样。结果显式输出候选、模式有效、生成无效、安全拒绝、安全接受与 fallback 分母。

## 3. 一手资料核验

- Diffusion Policy 官方仓库仍提供配置、三次训练聚合日志、checkpoint、归一化和异步真实环境接口；官方说明不能替代本书未运行的复现。
- LeRobot 当前 diffusion 配置把 `n_obs_steps`、`horizon`、`n_action_steps`、训练/推理 timestep、scheduler、sample clipping 和 padding mask 分开；未指定推理步数时回落到训练 timestep 数。
- openpi 当前仍把 π0 定义为 flow-based VLA、π0-FAST 定义为自回归 VLA，并仅为 π0.5 支持 flow matching head；官方单卡估算仍为推理大于 8 GB、LoRA 大于 22.5 GB、全量微调大于 70 GB，且提供 Docker 路线。

这些是一手项目接口与资源声明，不是本书实测性能。

## 4. 输入合同与一致性

第14章由 7 增至 14 个单元测试，全书由 213 增至 220 个。新增测试覆盖候选/batch 预算、非法计数、显式安全分母、全拒绝 fallback、空/非有限演示和样本、非有限 sampler 输入及 refinement rate 边界。实验卡升级为 fixture v2，正文、结果、manifest 与发布统计同步。
