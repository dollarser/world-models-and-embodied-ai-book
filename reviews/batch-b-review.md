# 批次 B 四类交叉审查：第13、14、15、20章

> 审查日期：2026-08-31
> 审查基线：`9b50660` 之后的批次 B 审查工作树
> 范围：4 章正文、manifest、4 张实验卡、4 组 fixture、结构化结果、Make/Docker 入口
> 结论：第13–15章达到 `reviewed`；第20章保持 `drafted`，等待第17、19章一致性审查

## 1. 状态边界

本次确认策略主线从行为克隆、动作分块、生成式动作到 VLA 执行合同能够连贯阅读；S 档实验和正文数字可追溯；自动驾驶内容位于各章正文；不要求 3D 视觉、GPU、机器人或商业 API。

本次没有训练 BC、ACT、Diffusion Policy、flow policy 或 VLA，没有下载 checkpoint/真实数据，也没有运行 LIBERO、MetaDrive、CARLA 或硬件。因此：

- `EXP-13-01/14-01/15-01/20-01` 均保持 `smoke`；
- 第13–15章的 GPU 状态保持 `pending`，上游资源数字仍是官方说明而非本书实测；
- 第20章虽然内容、代码和教学门通过，但第17章的世界模型辅助策略接口、第19章的仿真协议尚不存在，不能将一致性门写成通过；
- 整个批次 B 当前是“部分通过”，不是已经闭环。

## 2. 内容审查

| 章节 | 结论 | 关键边界 |
| --- | --- | --- |
| 第13章 | 通过 | 监督动作误差、闭环分布偏移和 chunk 陈旧延迟分开解释；解析误差累积不是 ACT 性能 |
| 第14章 | 通过 | 条件均值、多峰采样、diffusion 与 flow 接口分开；oracle straight flow 不参与方法优劣比较 |
| 第15章 | 通过 | VLM、VLA、世界模型、planner 与 safety layer 角色分开；动作 token、连续头和 flow head 落到同一执行合同 |
| 第20章 | 通过 | 成功率分子/分母、证据阶梯、效用/安全/效率/恢复指标齐全；固定 episode 表不是 benchmark |

审查日在官方一手来源复核了会漂移的案例：[OpenVLA](https://github.com/openvla/openvla) 的代码/模型许可边界与 LoRA 显存说明，[LeRobot](https://github.com/huggingface/lerobot) 的策略入口，[GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T) 的主干/动作头/资源说明，以及 [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) 的 4 个 suite、130 个任务。正文只保留对学习有用的稳定模式，并继续标记为上游事实或供应商声明。

## 3. 代码审查

四章共 24 个单元测试：第13章 4 个、第14章 7 个、第15章 9 个、第20章 4 个。四个 smoke 都使用 Python 标准库、零下载 fixture，并可由 Docker 入口执行。

第15章审查修复两个真实契约缺陷：

- Python 的 `bool` 原先会通过 `(int, float)` 类型检查，现在归一化、token 编码和执行网关都会拒绝布尔动作；
- packet 的 `prediction_horizon` 原先未与实际动作长度核对，现在篡改或缺失会产生 `prediction_horizon_mismatch`。

两项均有回归测试。固定 smoke 的五类 malformed packet 和指标未改变，新增门禁不被包装成新的模型性能结果。

## 4. 一致性审查

- 第13章的 action chunk、执行时域和闭环风险进入第14、15章；
- 第14章的生成式动作只负责候选分布，第15章负责 schema、反归一化、时间与安全网关；
- 第15章的 `prediction_horizon` / `execution_horizon` 与第13章 receding-horizon 语义一致；
- 第20章复用第4、9、15章的协议与证据层级，正文数字与 `EXP-20-01` 一致；
- manifest 中 `CLAIM/FIG/TAB/EXP` ID 与章节页、实验卡一致。

第13–15章在当前策略主线范围内通过一致性门，后续全书统稿仍会复核第3、5、17章接口。第20章必须等第17、19章成稿后再检查世界模型辅助策略、仿真版本、成功定义和失败日志，因此当前一致性状态为 `in_progress`。

## 5. 教学审查

- 章节从监督学习、条件分布和 JSON/schema 等 CV/软件背景概念出发，不假设机器人或 3D 经验；
- 每章都包含反例：开环小误差累积、均值落入双峰无效区、高层文本不可执行、同一结果表因协议变化而排名失真；
- 机器人与自动驾驶分别给出动作时域、轨迹约束、低频语言意图和闭环评测边界；
- S 档命令足以检验章节核心判断，M/L1/L2 均保持可选且未验证；
- 练习覆盖概念判断、代码修改、协议设计和跨领域迁移。

四章教学门均通过。

## 6. 验收命令

```bash
make ch13-smoke
make ch14-smoke
make ch15-smoke
make ch20-smoke
make check-strict
make docs-build
git diff --check
```

阶段提交前再次运行以上命令。宿主本地单元测试可用 `make ch13-test-local ch14-test-local ch15-test-local ch20-test-local` 快速定位失败，但不能替代 Docker 冷环境 smoke。

## 7. 保留问题与下一步

- 第13章尚未运行 LeRobot BC/ACT，也没有实测 24 GB 显存；
- 第14章尚未运行 Push-T/LIBERO 或 learned diffusion/flow 对照；
- 第15章尚未运行 VLA checkpoint、VLM API、机器人或远程推理；
- 第20章未把统计区间加入 smoke，且等待第17、19章后才能完成一致性审查；
- 下一阶段优先完成第17章的“世界模型帮助策略”与第19章的通用仿真合同，再回到第20章关闭批次 B。
