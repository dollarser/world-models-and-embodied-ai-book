# 批次 C 四类交叉审查：第3、10、11、12、19章

> 审查日期：2026-08-31
> 审查基线：`d3660fe` 之后的批次 C 审查工作树
> 范围：5 章正文、manifest、5 张实验卡、5 组 fixture、结构化结果、Make/Docker 入口
> 结论：第3、12、19章达到 `reviewed`；第10、11章保持 `drafted`，等待第5章生成式基础的一致性审查

## 1. 状态边界

本次确认没有 3D 视觉经验的读者可从像素/坐标桥接到表征、动作条件未来、三态 occupancy 和仿真合同；自动驾驶内容在五章正文中形成相机—BEV—动作反事实—驾驶闭环链路。S 档实验均为标准库、零下载 CPU fixture。

本次没有训练或运行 JEPA、视频模型、occupancy 网络、MuJoCo、MetaDrive、CARLA、Isaac Lab、机器人、车辆或 GPU。因此：

- `EXP-03-01/10-01/11-01/12-01/19-01` 均保持 `smoke`；
- 第10、11、12、19章 GPU 状态保持 `pending`，第3章为 `not_required`；
- 第10、11章的内容、代码和教学门通过，但它们依赖的第5章生成式基础尚未成稿，不能提前写成最终一致；
- 第3、12、19章只在当前已成稿依赖和 S 档证据范围内达到 `reviewed`，不表示完成真实 3D、仿真或 Sim2Real 复现。

## 2. 内容审查

| 章节 | 结论 | 关键边界 |
| --- | --- | --- |
| 第3章 | 通过 | 针孔、外参、BEV、运动学、反馈和 POMDP 只给最小桥接；坐标、单位、时间与动作 schema 明确 |
| 第10章 | 通过 | 像素重建、JEPA 表征、dense 分支和 probe 证据分开；论文/官方结果没有写成本书实测 |
| 第11章 | 通过 | ego action、世界事件、latent action 分开；renderer、simulator、planner 和策略评测合同不混用 |
| 第12章 | 通过 | free/occupied/unknown、动态空间、affordance 与可行动性边界明确；渲染质量不能替代碰撞合同 |
| 第19章 | 通过 | 仿真合同、六类 gap、系统辨识、留出验证和域随机化 support 形成闭环；Sim2Real 没有被过度声称 |

审查日使用一手研究/项目页面核对了会漂移的案例，包括 [V-JEPA 2.x](https://github.com/facebookresearch/vjepa2)、[DIAMOND](https://github.com/eloialonso/diamond)、[Occ3D](https://github.com/Tsinghua-MARS-Lab/Occ3D)、[MuJoCo/MJX](https://github.com/google-deepmind/mujoco)、[MetaDrive](https://github.com/metadriverse/metadrive)、[CARLA](https://github.com/carla-simulator/carla)、[Isaac Lab](https://github.com/isaac-sim/IsaacLab) 和 [RoboCasa](https://github.com/robocasa/robocasa)。正文只保留稳定架构、接口、许可和资源边界；闭源驾驶案例继续标为供应商声明。

## 3. 代码审查

五章共 32 个单元测试：第3章 6 个、第10章 5 个、第11章 6 个、第12章 7 个、第19章 8 个。结构化结果与同一 smoke 输出在 JSON 解析后结构和值精确相等；不把数组换行等空白差异误报为结果漂移。

本轮修复三个输入/安全合同缺陷：

- 第3章控制步数为零、负数、布尔值或非整数时，原先可能泄漏除零或隐式语义；现在统一拒绝；
- 第12章 `unknown_is_free=True` 原先也会把地图外路径当成未知可行；现在越界始终判为不安全；
- 第19章参数与动作原先会接受布尔或非有限浮点，随机化 support 未拒绝反向区间；现在均有显式校验和回归测试。

这些修复不改变任何固定指标，也不构成新的模型性能结论。Docker 服务继续使用只读仓库挂载，当前阶段不触发模型、数据或仿真资产下载。

## 4. 一致性审查

- 第3章的 frame/unit/timestamp/action schema 被第12章空间状态和第19章仿真合同复用；
- 第10章的 probe 只证明表征可读出性，第11章再增加动作干预，第12章再检查可行动空间，证据没有越级；
- 第11章的 action-conditioned rollout 与第17章 model exploitation、第19章独立仿真锚点接口一致；
- 第12章三态 unknown 语义进入第19章传感器/几何 gap 和自动驾驶安全边界；
- 第19章锁定机器人动力学优先 MuJoCo、驾驶 M 档默认 MetaDrive、CARLA 高保真可选，并已回填第17、20章。

第3、12、19章当前一致性门通过。第10、11章仍需在第5章完成后核对生成式目标、token/latent 表述和 teacher forcing 谱系，因此保持 `in_progress`；这不是用“批次通过”掩盖缺失依赖。

## 5. 教学审查

- 第3章提供 4–6 小时桥接门，第12章从二维射线进入三态空间，不假设 3D 先修；
- 每章都有可运行反例：尺度/外参错误、重建—probe 排名反转、action-blind 未来、unknown 假安全、名义仿真 gap；
- 自动驾驶不是独立附录，而是分别覆盖坐标、状态 probe、ego action/他车响应、BEV occupancy 和 MetaDrive/CARLA 分工；
- S/M/L1/L2 资源逐级可选，默认不要求硬件或大型下载，GPU 未运行结果保持 `pending`；
- 练习覆盖概念、代码、实验设计和机器人/驾驶迁移。

五章教学门通过。

## 6. 验收命令

```bash
make ch03-smoke
make ch10-smoke
make ch11-smoke
make ch12-smoke
make ch19-smoke
make check
make docs-build
git diff --check
```

阶段提交前再次运行以上命令，并解析比较五个 `results/` JSON 与 smoke 输出的结构和值。Material for MkDocs 的上游 MkDocs 2.0 公告不是本项目构建失败；严格构建必须以 0 退出。

## 7. 保留问题与下一步

- 第3章没有真实标定、畸变、接触、动力学或多传感器同步；
- 第10、11章等待第5章后关闭一致性门，且未运行 checkpoint、视频数据或 GPU；
- 第12章没有真实 RGB-D/驾驶 occupancy、学习模型或传感噪声；
- 第19章没有安装仿真器、下载资产或完成真实系统辨识；
- 批次 D 应复用本批次的动作反事实、unknown、simulator gap 和独立真实性锚点，再回到第20章关闭跨批次一致性门。
