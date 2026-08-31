# 批次 A 四类交叉审查：第2、4、6、9章

> 审查日期：2026-08-31
> 审查基线：`bebf195` 之后的批次 A 审查工作树
> 范围：正文、manifest、4 张实验卡、4 组 fixture、结构化结果、Make/Docker 入口
> 结论：四章达到 `reviewed`；四个实验仍保持 `smoke`

## 1. 状态边界

本审查只确认：当前正文能够面向有 CV 基础、无 3D/机器人前置经验的读者使用；S 档命令和指标链路可运行；声明、图表、实验和限制能够互相追溯。

本审查没有执行神经世界模型训练、真实 LeRobot 数据审计、WorldArena、MetaDrive/CARLA、机器人硬件或 GPU 实验。因此：

- `EXP-02-01/04-01/06-01/09-01` 不升级为 `experimented` 或 `reproducible`；
- 第6章 GPU 状态仍为 `pending`；
- 第2、4、9章只因当前契约不需要 GPU 而标记 `not_required`；
- 上游论文结果没有被改写为本书实测。

## 2. 内容审查：通过

| 章节 | 检查重点 | 修复与结论 |
| --- | --- | --- |
| 第2章 | 世界模型定义、VLA/视频/仿真器/数字孪生边界 | 四轴分类与术语基线一致；数字孪生的动作和学习动力学改为 scope-dependent，不再强制二元判断 |
| 第4章 | episode、动作时序、切分、统计与资源协议 | `o_t → a_t → o_{t+1}` 语义明确；真实数据、隐私和许可限制保留 |
| 第6章 | prior/posterior、RSSM、one-step/multi-step | 新增稳定声明和图表 ID、结果边界、资源档位及自动驾驶闭合速度案例 |
| 第9章 | 感知、干预、决策和闭环证据 | E0–E4 用途层级与第2章定义、第4章协议和第6章误差边界一致 |

关键系统卡来源在审查日回到一手页面核对，包括 [VideoGPT](https://arxiv.org/abs/2104.10157)、[Genie](https://arxiv.org/abs/2402.15391)、[DreamerV3](https://www.nature.com/articles/s41586-025-08744-2)、[pi0](https://arxiv.org/abs/2410.24164)、[MuJoCo](https://mujoco.readthedocs.io/)、[NIST Digital Twins](https://www.nist.gov/digital-twins) 和 [CARLA](https://arxiv.org/abs/1711.03938)。这一步核对的是分类元数据，不是运行复现。

## 3. 代码审查：通过

审查覆盖 4 个 S 档实验入口和 15 个章节单元测试：

- 第2章：4 个测试，检查八类覆盖、VLA 边界、证据限制和数字孪生 scope-dependent 字段；
- 第4章：5 个测试，检查有效 fixture、group 泄漏、动作对齐、统计泄漏和非数值动作；
- 第6章：3 个测试，检查动作进入 prior、posterior 修正和 rollout gap；
- 第9章：3 个测试，检查动作盲区和指标排序反转。

审查中修复了第4章的一个真实缺陷：非数值动作原先可能触发 Python 类型比较异常；现在返回 `invalid_action_type` 结构化问题并有回归测试。Docker 服务均使用只读仓库挂载和固定 Python 3.12 slim digest。

## 4. 一致性审查：通过

- `terminology.md` 中环境、状态、信念状态、动作、策略、世界模型、开环和闭环的定义在四章中没有冲突；
- 第2章的“用途决定边界”进入第9章 E0–E4 评测层级；
- 第4章的 episode、时间和 group split 约束被第6、9章实验边界引用；
- manifest 注册的 `CLAIM/FIG/TAB` ID 均存在于正文；
- 实验卡的 `claim_ids` 必须属于相应章节 manifest，已加入严格校验；
- 章节页状态必须与 manifest 一致；达到 `reviewed` 后，正文必须记录四项通过和存在的审查文件。

## 5. 教学审查：通过

- 四章均声明已具备、本章补齐和不要求的知识；不假设 3D 视觉或机器人经验；
- 每章从 CV 读者熟悉的图像、视频、指标或数据切分建立桥梁；
- 自动驾驶内容位于第2、4、6、9章正文，不依赖独立附录；
- 每章包含概念题、代码/协议题和迁移分析题；
- smoke、论文结果、待验证训练和部署安全证据被明确区分。

## 6. 验收命令

```bash
make check
make ch02-smoke
make ch04-smoke
make ch06-smoke
make ch09-smoke
make docs-build
git diff --check
```

阶段提交前必须再次运行这些命令。Material for MkDocs 输出的 MkDocs 2.0 上游公告不计作项目内容警告；`mkdocs build --strict` 必须以 0 退出。

## 7. 保留问题与下一批输入

- 第2章系统卡尚未为每个上游仓库锁定可运行 commit；当前只用于概念分类；
- 第4章未审计真实数据、视频解码、多传感器标定、隐私和许可；
- 第6章仍需 PyTorch mini-RSSM、24 GB 单卡资源实测和训练收敛证据；
- 第9章 WorldArena 与 2026 年预印本只完成资料核查；
- 批次 B 编写第13、14、15、20章时，必须复用本批次的术语、实验卡和 E0–E4 证据层级。
