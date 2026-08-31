# 批次 D 四类交叉审查：第8、16、17、18、20、21章

> 审查日期：2026-08-31
> 审查基线：`0617dae` 之后的批次 D 审查工作树
> 范围：6 章正文、manifest、6 张实验卡、6 组 fixture、结构化结果、Make/Docker 入口
> 结论：六章均在当前 CPU/S 档证据范围内达到 `reviewed`；GPU、仿真、模型和硬件状态不变

## 1. 状态边界

本批次闭合“imagined target → 跨本体数据 → 世界模型效用/漏洞 → VLA 后训练 → 独立评测 → 部署网关”链路。自动驾驶内容分别落在 imagined policy、跨车队 schema、world-model 四角色、后训练闭环真值、指标协议和最小风险动作正文中，不依赖独立附录。

本次没有训练 Dreamer、VLA、adapter、critic 或 learned world model，没有下载 LIBERO/驾驶数据或 checkpoint，也没有运行 MetaDrive、CARLA、ROS、机器人、车辆或 GPU。因此：

- `EXP-08-01/16-01/17-01/18-01/20-01/21-01` 均保持 `smoke`；
- 第8、16、17、18、21章 `gpu_status` 保持 `pending`，第20章保持 `not_required`；
- `reviewed` 只表示正文、S 档代码、实验结果和跨章合同通过审查，不表示完整方法复现、实时性或安全认证；
- 24 GB 单卡与最多 2×80 GB 只作为可选上限，所有未实测配置继续标为待验证。

## 2. 内容审查

| 章节 | 结论 | 关键边界 |
| --- | --- | --- |
| 第8章 | 通过 | real replay 与 latent imagination 分开；λ-return、continuation 和 model bias 只作解析接口，不冒充 Dreamer 训练 |
| 第16章 | 通过 | mixture、canonical action、adapter/LoRA/蒸馏和跨车队 schema 分开；shape 相同不等于语义兼容 |
| 第17章 | 通过 | 世界模型五种用途及评测替身风险各有对应证据；平均 prediction score 不授权策略 |
| 第18章 | 通过 | SFT、离线重加权、物理仿真 RL、world-model RL 与人类纠正分开；WAM 按四类接口而非名称分类 |
| 第20章 | 通过 | 任务总体、成功定义、分母、效用/安全/效率/恢复和证据阶梯完整；已补齐第17/19章真实性锚点 |
| 第21章 | 通过 | sensor age、端到端 latency、chunk freshness、watchdog、fallback 与本体特定 MRM 分开；不构成认证 |

会漂移的研究案例以论文、作者项目或官方仓库为锚点：DreamerV3/Dreamer 4、Open X-Embodiment/DROID/LeRobot、V-JEPA 2/TD-MPC2/WorldGym、RIPT-VLA/VLA-RFT/World-Gymnast/WoVR、LIBERO/MetaDrive/CARLA，以及 ROS 2/Autoware。论文数字和供应商能力均保持上游证据标签，没有写成本书实测。

## 3. 代码审查

六章共 40 个单元测试：第8章 7 个、第16章 9 个、第17章 6 个、第18章 7 个、第20章 4 个、第21章 7 个。六个 smoke 均使用标准库和零下载 fixture；结果 JSON 与 smoke 输出的解析结构和值精确一致。

本轮修复第16章一个真实合同缺陷：跨本体 adapter 原先只检查夹爪范围，布尔、NaN/Inf、零/负单位尺度、非法 polarity、空池化和不完整 action 可能进入换算或触发非结构化异常。现在 adapter metadata、raw/canonical action 和 pooling 都显式校验，并新增 2 个回归测试。固定 `EXP-16-01` 数字未改变。

其余五组 fixture 的边界检查覆盖：第8章长度/有限值/discount/λ，第17章未知动作与 terminal reuse，第18章权重/ESS/support，第20章未知 protocol，第21章配置、延迟、动作和 horizon。未把新增输入拒绝包装成模型性能提升。

## 4. 一致性审查

- 第8章定义 imagined reward/continuation 如何进入 target；第17章展示 policy 如何利用模型盲区；第18章据此要求 learned-simulator RL 保留独立回查；
- 第16章 canonical schema 与 mixture/provenance 进入第18章后训练数据和第21章执行网关，raw action 不跨本体直接汇总；
- 第17章的五种用途与第18章 WAM 四种实现路径正交：前者回答“用于什么”，后者回答“怎样连接未来与动作”；
- 第19章已经锁定物理 simulator 合同，第20章据此关闭真实性与可比性门，第21章再把评测字段转成 deadline/fallback 条件；
- 第20章不再等待第17/19章：world-model exploitation、sim gap、任务总体和失败日志已逐项核对；
- 自动驾驶链路统一为日志/MetaDrive/CARLA/learned model 分层取证，碰撞和道路边界不被 reward 抵消，所有 policy action 最终进入车辆动力学、时效和最小风险网关。

六章 manifest 中的 `EXP/CLAIM/FIG/TAB`、资源档位、GPU 状态、正文状态和审查路径一致，因此一致性门通过。

## 5. 教学审查

- 第8章从三步 target 进入 imagined learning，第18章从四条轨迹进入 post-training，不要求 RL 数学或 GPU；
- 第16章用两维动作说明单位/极性，第20、21章用固定 episode/packet 说明协议和系统边界；
- 每章都有反例或失败：终止泄漏、raw pooling、模型捷径、coverage 塌缩、协议漂移、尾延迟与过期 chunk；
- 自动驾驶不是补充阅读，而是每章稳定接口的同构案例；
- S/M/L1/L2 逐级可选，默认 S 档即可完成核心练习，硬件和商业 API 都不是必需条件。

六章教学门通过。

## 6. 验收命令

```bash
make ch08-smoke
make ch16-smoke
make ch17-smoke
make ch18-smoke
make ch20-smoke
make ch21-smoke
make check
make docs-build
git diff --check
```

阶段提交前再次运行以上命令，并比较六个 `results/` JSON 与 smoke 输出。MkDocs Material 关于未来 MkDocs 2.0 的上游警告不改变当前严格构建的 0 退出要求。

## 7. 保留问题与下一步

- 第8章没有训练 world model/actor/critic；
- 第16章没有真实跨本体数据、adapter 训练或迁移矩阵；
- 第17、18章没有 learned simulator/VLA/RL/critic、真实 policy ranking 或 LIBERO；
- 第20章 fixture 尚未加入统计区间，第21章没有真实墙钟、调度器、网络或 ROS；
- 批次 D 通过后进入第1章导论和第22章综合项目，最后执行全书术语、图表、链接、结果与发布构建审查。
