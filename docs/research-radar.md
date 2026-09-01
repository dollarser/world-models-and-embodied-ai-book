# 研究雷达：怎样阅读快速演进的世界模型研究

> 最近核查日期：2026-09-02；各卡以机器登记的 `last_verified` 为准
> 机器登记：`specs/research-radar.json`  
> 当前状态：只完成一手来源与公开资产审计；没有运行模型、数据、GPU、仿真、机器人或车辆

这页不是“最新模型排行榜”，也不把论文摘要改写成本书结果。它回答三个更稳定的问题：近期研究正在改变什么接口；这些变化应回到哪一章理解；需要什么新证据，才值得修改稳定正文。

## 一眼看懂：近期工作的共同方向

| 方向 | 代表入口 | 真正的新问题 | 不能越过的证据边界 |
| --- | --- | --- | --- |
| 更大、更快的 learned simulator | [Dreamer 4](https://arxiv.org/abs/2509.24527)、[Interactive World Simulator](https://arxiv.org/abs/2603.08546) | 能否在足够长、足够快的动作条件 rollout 中训练或比较策略 | 推理实时不等于训练便宜；长视频不等于物理正确；相关性不等于绝对校准 |
| 表征与生成接口扩展 | [V-JEPA 2.1](https://arxiv.org/abs/2603.14482)、[Cosmos 3 快照 `9aa98e5`](https://github.com/NVIDIA/cosmos/tree/9aa98e5a0773a5558f07d2699e640858f7ca8827) | dense representation 和统一 action 接口怎样服务状态估计、预测与控制 | feature 可读不等于动作转移正确；接口含 action 不等于 simulator fidelity |
| 世界模型进入策略训练与评测 | [GE-Sim 2.0](https://arxiv.org/abs/2605.27491)、[A2World](https://arxiv.org/abs/2606.29501)、[Riemann-1.0](https://arxiv.org/abs/2608.27033) | learned rollout、state decoder、reward/judge、policy head 和共享预训练怎样组成闭环 | 共用权重或接口不等于policy与simulator两种能力都已独立校准；上游真实结果不是本书复现 |
| 跨本体从表示假设进入受控反例 | [OSCAR](https://arxiv.org/abs/2606.04463)、[XEWorld](https://arxiv.org/abs/2608.05799) | skeleton、pixel action或向量动作是在迁移动力学，还是只在匹配外观 | 受控失败只约束被测模型；视觉对齐不替代可执行动作、接触与动力学证据 |
| “评测器也会错”成为显式研究对象 | [WorldArena 2.0](https://arxiv.org/abs/2605.17912)、[KineBench](https://arxiv.org/abs/2607.19876) | 模态、用途、平台与动作落地层怎样分别归因 | 更完整的 benchmark 仍有作用域；去掉 IDM 不会消除 pose extractor 和 simulator 误差 |
| 部分可观测性从单一 mask 转向 memory-improvable 诊断 | [POBAX](https://arxiv.org/abs/2508.00046) | 更多 state 信息或 memory 是否在其他条件近似不变时关闭清晰 performance gap | 一个任务有 gap 不代表模型学会正确记忆，也不覆盖所有 state aliasing 类型 |

这六行共同强化了全书主线：模型输出必须经过“表征—动作条件转移—用途—独立 outcome”逐级取证。它们没有推翻第2章的定义、第9章的评测阶梯或第17章的用途边界。

## 十二张活页卡

### Dreamer 4：规模化想象训练

论文报告用 shortcut forcing 与高效 transformer 让世界模型在单 GPU 上进行实时交互推理，并在 Minecraft 离线数据中训练行为。它最适合接回第6章的 latent state、第8章的 imagined learning 和第17章的 simulator utility。

阅读时要分开三个量：完整训练资源、交互推理资源、最终任务证据。论文中的“单 GPU 实时”描述的是其指定推理路径，不能推成“24 GB 单卡可完整训练”，也不能从 Minecraft 直接推到机器人操作或自动驾驶。

### POBAX：先证明任务真的需要 memory

POBAX 把部分可观测性拆成多种 state aliasing 类型，并要求任务在更多或更少 state 信息之间具有可解释的 performance gap。这个设计接回第2章的新反例：若 current-only 与 history-aware oracle 没有差距，训练更大的 recurrent policy 也很难说明改进来自记忆。

但 memory-improvable 是 benchmark 属性，不是算法能力证书。固定任务上存在 gap，只说明有信息可由历史恢复；还要分别验证模型是否学到正确 cue、能保持多久、是否依赖泄漏，以及能否迁移到遮挡、未知意图、定位等其他 aliasing。官方仓库已锁到[快照 `a5e1d62`](https://github.com/taodav/pobax/tree/a5e1d62d14e4efe783885b9d4f19cffa2a568eec)，当前没有安装 JAX、下载可选渲染依赖或运行其训练。

### V-JEPA 2.1：dense feature 不是完整 world state

论文把 dense predictive loss、deep self-supervision 与图像/视频统一训练列为关键变化，官方仓库提供代码符号和 checkpoint 链接。它能丰富第10章的表示学习谱系，但不会改变本书的门禁：状态 probe、时间 shift、动作反事实和闭环用途必须分开。

2026-09-02 的源码预检同时发现，当前官方 HEAD/锁定快照 `204698b` 的 Hub loader 把下载基址设为测试用 `localhost:8300`。因此该卡仍可按 `R1` 表示“部分公开资产可审计”，却不能升级为 `R2`，也不能把 `torch.hub.load(..., pretrained=True)` 写成普通新环境已可执行命令。公开权重存在、loader 兼容和本书实测是三个状态。

对没有 3D 经验的读者，正确入口仍是第3章坐标/深度合同和第10章的 CPU probe，而不是先下载大型 checkpoint。dense feature 可以帮助深度、抓取或导航 probe；这些任务成绩仍不自动证明 counterfactual dynamics。

### Cosmos 3：统一 action 接口的价值与边界

官方仓库把 text、vision、sound 与 action 放进统一物理 AI 平台，并同时列出时间一致性、action-state consistency、3D 与物理合理性限制。这个“能力和限制写在同一接口”的做法很适合第11章：读者应审计动作字段、生成时域与限制，而不是只看样片。

Action cookbook 还暴露一个容易被安装说明掩盖的实验变量：Generator 默认依赖 gated Guardrail，也允许显式关闭。关闭后得到的是另一条安全处理配置，必须登记并限制声明；仓库的 OpenMDW-1.1 也不能简写为 MIT。资产“可见”不等于无需授权、许可一致或默认安全路径已运行。

自动驾驶中也一样：能接收转向或轨迹条件，只证明存在干预入口。还需核对其他交通参与者如何响应、道路/碰撞怎样计算、模型 return 是否与 MetaDrive/CARLA 或真实日志一致。

### WorldArena 2.0：从视觉分数扩展到用途与平台

论文把评测沿 modality、functionality、platform 三轴扩展，包含视觉—触觉、policy optimization 以及模拟和真实机器人设置。它支持第9章的教学判断：感知质量、策略评估、规划和交互式训练不是同一个完成标准。

但“覆盖面更广”仍不等于一个总分可以跨用途解释。实际采用前必须冻结任务、模型版本、输入模态、聚合规则、无效运行与真实平台协议；本书目前只核对论文和项目页，保持 `R0–R1`。

### KineBench：闭环评测的归因链

KineBench 针对“生成视频先经 IDM 反推动作，再进 simulator”产生的归因混淆，改用显式 6D 末端位姿提取与运动学指标。其最重要的教学价值不是某个榜单数字，而是提醒读者把 evaluator 拆开：视频模型、pose extractor、坐标变换、动作执行器和 physics simulator 都会贡献误差。

因此“IDM-free”应理解为减少一种混淆，而不是 ground-truth-free。若 pose extractor 在遮挡、反光或新本体上漂移，闭环结果仍不能全部归因给世界模型。

### GE-Sim 2.0：transition、state expert 与 world judge 三段误差

论文把 action-conditioned rollout、从视频 latent 解码状态的 state expert、为任务评分的 world judge，以及加速推理组合起来。它正好对应第17章的代理评测分解和第18章的 learned-simulator 后训练。

如果策略在该系统内变好，至少还有三个待回答问题：transition 是否在候选策略分布上准确；state expert 是否保持单位/坐标/接触语义；world judge 是否会被 policy exploit。论文报告的 H100 时延和真实增益都保留为上游结果，不是本书资源或性能数据。

### Interactive World Simulator：吞吐、稳定与真实性是三张表

论文报告 consistency-model 路线、长时交互、RTX 4090 吞吐，以及 world-model 与真实策略评测的相关性。阅读时应把这些证据拆成：生成吞吐与 deadline、长时 rollout 的数值/视觉稳定、策略排序相关、绝对成功率校准和新策略泛化。

相关性只支持已验证策略总体中的筛选用途。引入新的 policy、任务、物体或接触分布后，仍要回到第17章的 prospective calibration 与 support gate。

### OSCAR：跨本体视觉条件不等于动作可互换

OSCAR 用 2D kinematic skeleton 作为跨机器人/人手的动作条件，并在 Cosmos-Predict2.5 基础上训练。它为第16章提供了一个很好的假设：先把不同本体的可见运动投影到共享表示，再学习视频转移。

但 skeleton 没有自动携带力、接触、关节/速度限制、控制时延和可逆 action mapping。它可以作为视觉条件对齐层，不能替代第3章动作 schema、第16章 adapter identity 或第21章执行网关。论文使用的 GH200 路径也不属于默认 24 GB 单卡实验。

### XEWorld：把“未见本体”从口号变成隔离变量

XEWorld在物理场景保持一致时留出整台机器人，分别检查视觉质量、机器人形态、运动学轨迹和动作—时间对齐。论文在其被测模型上报告：泛化更受视觉相似度而非运动学相似度支配；零样本渲染需要pixel-space动作与显式时空对齐；少样本恢复新外观又可能遗忘已见本体。这组设计为第16章提供了比“换个机器人测一下”更严格的反例结构。

边界同样重要：这些是 `arXiv:2608.05799v1` 在指定模型和测试床上的作者结果，不是所有latent/vector action都必然失败的定理。协议设计已进入第16章，但本书没有取得版本化代码/数据或运行模型；作者结果仍保持 `R0`。

### Riemann-1.0：一个模型、两种角色仍需两套证据

Riemann-1.0把多视角观测、机器人state和本体特定action放进因果自回归序列，并同时声明在线policy与action-conditioned simulator两种角色。它把第15章的可执行动作和第17章的代理仿真放到同一个接口里，因而特别适合追问：训练目标、推理路径、时延和校准是否对两种用途分别成立。

截至2026-09-02，本书只核对 `arXiv:2608.27033v1`；代码、权重和数据都登记为unknown。论文中的数据规模、benchmark和真实机器人数字全部是上游报告，既不是本书结果，也不能推出24 GB路径。没有版本化资产前，该卡保持 `monitor/R0`，不进入稳定章节。

### A2World：开源的是哪一段，要逐项回答

A2World从action-to-video预训练出发，再分成history-aware的A2World-sim和联合video-action的A2World-policy。[ECCV 2026官方收录页](https://eccv.ecva.net/virtual/2026/poster/3656)确认论文已接收；官方仓库快照[`077e10a`](https://github.com/LogosRoboticsGroup/A2World/tree/077e10ad6cee07342b5e779f11fea78247584834)提供Apache-2.0代码、world-model入口和部分checkpoint元数据。这让“同一动力学先验能否服务simulator与policy”有了可审计接口，而不只是摘要措辞。

当前发布仍以world-model组件为重点，外部base weights、数据集、policy路径和论文结果不是一个自动闭合的复现包。本书只完成README、许可、锁定源码和入口的零下载预检，没有拉取checkpoint、安装环境、运行GPU或验证24 GB适配。因此该卡保持 `R1` 的资产审计；第17章已经吸收“共享先验、两条分支独立验收”的证据设计，但这不构成policy或simulator能力复现。

## 怎样决定是否更新正文

新工作只在满足下列至少一项时进入稳定正文：

1. 改变本书的核心定义或证明现有分类漏掉了独立能力轴；
2. 提供新的可复用失败机制，且不能被现有反例表达；
3. 发布足够完整的代码、权重、数据和协议，使可复现状态可从 `R0` 升级；
4. 独立证据改变了模型用途、资源或安全边界；
5. 新接口已经成为多个主流开源项目共同采用的稳定模式。

只更新模型版本、排行榜或供应商能力时，更新机器登记和活页卡，不重写章节骨架。每次更新还要说明旧条目为何保留、替换或删除。

## 当前最值得追踪的证据缺口

- learned simulator 对**新增策略**的 prospective ranking，而不是对参与调参的固定策略回顾性相关；
- transition、state decoder、reward/judge、action grounding 已有第17章 S 档单故障归因账；仍缺 learned pipeline 上的组件校准、交互项和端到端误差预算；
- 24 GB 单卡内真实可执行的最小配方，以及 checkpoint 冷启动下载、loader/权重兼容、磁盘、峰值显存和墙钟；
- 机器人与自动驾驶中按场景严重度分桶的 model exploitation、uncertainty gate 和 fallback 后果；
- 代码、权重、数据、benchmark 与许可证能否作为同一版本化研究对象被第三方取得。

这些缺口决定后续优化顺序：优先补能改变结论的证据，不以更多模型名称替代更强实验设计。
