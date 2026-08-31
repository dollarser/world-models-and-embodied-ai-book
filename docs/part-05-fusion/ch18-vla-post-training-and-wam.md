# 第18章 VLA 后训练、长时序与 World-Action Models

> 状态：`reviewed`
> 资料核查日期：2026-08-31
> 关联实验：`EXP-18-01`
> 关联声明：`CLAIM-18-01`～`CLAIM-18-06`
> 关联图表：`FIG-18-01` / `TAB-18-01` / `TAB-18-02` / `TAB-18-03`
> 资源档位：S / M / L1 / L2
> GPU 状态：待验证

## 本章契约

### 核心问题

监督微调（SFT）之后，怎样利用成功/失败、稀疏奖励、人类纠正、物理仿真或 learned world model 继续改进 VLA？长时任务为什么不能靠无限加长 action chunk？“World-Action Model”究竟是可交互世界模型、带未来预测辅助目标的策略，还是联合生成未来与动作的模型？

### 先修知识

- 已具备：第8章 imagined actor/critic target，第13章分布偏移与动作块，第15章 VLA/action schema，第16章跨本体适配，第17章 world-model exploitation；
- 本章补齐：SFT 后训练路线、奖励与 credit assignment、离线重加权、交互式 RL、层级/记忆/恢复，以及 World-Action Model 接口分类；
- 不要求：RL 推导、3D 视觉、LIBERO、VLA checkpoint、GPU、机器人或自动驾驶硬件。

### 非目标

- 不把 `EXP-18-01` 称为 offline RL、RIPT-VLA 或 VLA-RFT 复现；
- 不把成功轨迹权重提高等同闭环成功率提高；
- 不把 VLM reward、world-model reward 或 simulator reward 默认当真值；
- 不把长 context、长 action chunk 或长视频自动称为 long-horizon competence；
- 不把所有联合视频—动作网络强行归入一个 WAM 定义；
- 不要求购买硬件，也不声称上游多 GPU 配方已适配到本书上限。

### 学完后的可验证产出

读者应能为一个后训练系统登记 policy、interaction source、reward/verifier、advantage/weight、support constraint 和独立 evaluation；计算 reward-weighted behavior target 与 effective sample size；设计带 phase、memory、replan 和 recovery 的长时任务；按输入输出和因果接口判别 WAM。

## 18.1 SFT 之后还缺什么

SFT 最大化示范动作在观察和指令下的似然：

\[
\mathcal L_{\text{SFT}}(\theta)
=-\sum_{(o,l,a)\in D}\log \pi_\theta(a\mid o,l).
\]

它回答“数据中的操作者做了什么”，不直接回答动作导致的后果、失败能否恢复、多个可行动作哪个回报更高，或闭环偏离示范后怎样回到任务。后训练引入 outcome，但也增加了新的污染源：reward 定义、数据收集 policy、优势估计、环境真实性和更新后 distribution shift。

`CLAIM-18-01`（fact）：VLA 后训练的完成定义至少包含 interaction source、reward/verifier、credit/advantage、policy support、更新算法和独立闭环评测；“用了 RL”不是足够的实验说明。

```mermaid
flowchart LR
    B[SFT policy + versioned action schema] --> R[rollout source]
    R --> P[physical simulator]
    R --> W[learned world model]
    R --> H[real/human-corrected interaction]
    P --> T[trajectory + reward + termination]
    W --> T
    H --> T
    T --> C[credit / advantage / weights]
    C --> U[policy update + support/KL constraint]
    U --> E[held-out closed-loop evaluation]
    E -->|failure and new coverage| R
    G[independent safety gate] --> E
```

*FIG-18-01：VLA 后训练的审计闭环。来源：本书原创，MIT，2026-08-31。learned world model 与独立评测环境必须分别登记。*

## 18.2 五条后训练路线

| 路线 | 新信号 | 优势 | 主要失效 |
| --- | --- | --- | --- |
| 离线奖励重加权/过滤 | 固定轨迹 outcome | 不新增交互，易审计 | 样本集中、coverage 丢失、confounding |
| Offline RL / critic | 固定 transition + reward | 可学习多步 value | OOD action 过估计、bootstrap 偏差 |
| 物理仿真在线 RL | simulator transition/reward | 可闭环探索和重复 | sim gap、privileged reward、并行成本 |
| learned-world-model RL | predicted future/reward | 从真实视频动作数据扩展想象 | hallucination、reward hacking、策略利用模型 |
| 人类纠正/真实交互 | intervention、preference、outcome | 接近部署分布 | 昂贵、有风险、标注/操作者偏差 |

*TAB-18-01：后训练路线按数据和错误源分类。可组合路线，但每种信号要单独做 ablation。*

离线 reward-weighted behavior cloning 可写成：

\[
\mathcal L_{\text{RWBC}}
=-\frac{1}{\sum_i w_iT_i}
\sum_i w_i\sum_{t=1}^{T_i}\log\pi_\theta(a_{i,t}\mid o_{i,\le t},l_i).
\]

权重可以来自 episode success、return、advantage、preference 或人工评级。它仍是加权监督学习；没有 Bellman backup、policy interaction 或 actor objective 时，不应标成 offline RL。

稀疏 episode reward 会把同一权重施加给长轨迹内所有动作：成功轨迹中的偶然动作被奖励，失败轨迹中正确前缀和恢复动作被惩罚。解决 credit assignment 需要阶段状态、dense progress、value/advantage、counterfactual 或更细粒度 verifier，但每一种又可能引入 reward misspecification。

## 18.3 EXP-18-01：target 改善与 coverage 损失同时发生

S 档 fixture 有四条两阶段标量轨迹：两条成功、两条最终失败但包含 `recover` 事件。成功轨迹动作均值 `(0.25,0.75)` 被手工设为参考；这只是教学 oracle，不是真实任务最优策略。

```bash
make ch18-test-local
make ch18-smoke-local
make ch18-smoke
```

| 权重 | action target | reference MAE | ESS | recovery mass |
| --- | --- | ---: | ---: | ---: |
| 全部 1 | `(0.55,0.45)` | 0.30 | 4.0 | 0.50 |
| 成功 3、失败 1 | `(0.40,0.60)` | 0.15 | 3.2 | 0.25 |
| 只保留成功 | `(0.25,0.75)` | 0.00 | 2.0 | 0.00 |

*TAB-18-02：`EXP-18-01` 固定 reward reweighting 结果。ESS 为 \((\sum_i w_i)^2/\sum_i w_i^2\)，recovery mass 是归一化权重，不是恢复成功率。*

`CLAIM-18-02`（result）：固定成功权重从 1 增至 3 后，两阶段 target 从 `(0.55,0.45)` 移到 `(0.40,0.60)`，相对手工成功参考的 MAE 从 0.30 降到 0.15。代码没有训练或评测 policy，因此不能声称成功率改善。

`CLAIM-18-03`（result）：同一重加权把 ESS 从 4.0 降到 3.2，并把 recovery 样本权重占比从 0.50 降到 0.25；只保留成功时 ESS=2、recovery mass=0。target 更接近参考与 coverage 下降在此 fixture 中同时发生。

fixture 还用逐阶段数据最小/最大值拒绝 `(-0.1,1.1)` 这一 OOD proposal。范围内不代表安全或可达，只是最弱的 behavior-support 检查。

## 18.4 交互式后训练：稀疏成功信号也有代价

[RIPT-VLA](https://arxiv.org/abs/2505.17016)用稀疏二元 success 做 VLA interactive post-training，并采用动态 rollout sampling 与 leave-one-out advantage estimation；作者[代码仓库](https://github.com/Ariostgx/ript-vla)提供 QueST/OpenVLA-OFT + LIBERO 路线 `[A/O,R1]`。它展示的是交互环境中的 RL，不是 learned world model 路线。

二元 success 避免手工 dense reward 的部分偏置，却没有消除 credit assignment：需要同任务/初态下足够多的成功与失败 rollout 才能形成可用组内相对信号。若一组全失败或全成功，优势退化；若 policy 更新太快，旧 rollout 与新 policy 不匹配；若 simulator success 使用 privileged state，真实部署未必拥有同一 verifier。

人类纠正可记录 intervention 前观察、模型原动作、纠正动作、触发原因和恢复结果。只保存纠正动作会丢失“为何接管”和 policy-induced state，无法区分动作学习与数据选择效应。高风险机器人/车辆必须先用保守 controller 和安全员协议限定探索范围。

## 18.5 在 learned world model 中后训练

这一路线继承第8章 imagined learning，却把 policy 扩展到大视觉—语言—动作模型，常用生成视频、VLM verifier 或目标参考构造 reward。

- [VLA-RFT](https://arxiv.org/abs/2510.00406)用数据驱动 world simulator 预测动作条件视觉未来，并从目标参考构造 trajectory-level 学习信号 `[A,R0]`；
- [World-Gymnast](https://arxiv.org/abs/2602.02454)让 VLA 在 action-conditioned video world model 中 rollout，再由 VLM 给任务完成 reward；其[作者仓库](https://github.com/world-gymnast/world-gymnast)公开 OpenVLA-OFT 训练入口 `[A/O,R1]`；
- [WoVR](https://arxiv.org/abs/2602.13977)不假设 world model 完美，而用可控动作条件模型、Keyframe-Initialized Rollouts 与 world-model/policy co-evolution 缩短有效误差链 `[A,R0]`。

这些 2025–2026 工作属于快速变化的方法簇，论文结果是上游证据，不是本书实测。三者即使都叫 world-model RL，也不共享 simulator、reward、policy backbone、rollout horizon 或真实回查协议，不能直接横比摘要成功率。

最低审计矩阵是：SFT baseline、reward reweight baseline、物理 simulator RL、learned simulator RL，以及相同最终 policy 在独立环境的闭环评测。还要报告 model-only return、外部 return、策略排序、hallucination、VLM reward agreement、OOD 和迭代后 simulator gap。

## 18.6 长时序不是把短时策略重复更多次

长任务同时包含三种时间尺度：高频控制、技能/子任务和全局任务进度。单纯增大 action chunk 会减少反馈频率；单纯扩展视觉 context 会增加计算并混入无关历史；单纯让 VLM 写长计划则可能在第一步失败后继续执行过期文本。

一个稳定的层级合同包含：

1. planner 低频输出版本化 subgoal 和完成条件；
2. executor 高频产生短 action chunk，并可被中断；
3. progress estimator 用当前观察判定完成、失败、卡住或不确定；
4. memory 保存已完成阶段、关键对象状态、失败与纠正，而非无界堆叠全部帧；
5. recovery/replan 在证据不匹配时重置 subgoal，不伪造任务进度。

[MindExplore](https://openaccess.thecvf.com/content/ICCV2025/html/Li_Towards_Long-Horizon_Vision-Language-Action_System_Reasoning_Acting_and_Memory_ICCV_2025_paper.html)是 ICCV 2025 的层级 reasoning—acting—memory 案例 `[P,R1]`。它支持“分层和反馈是可行架构模式”，不能证明特定沙地系统结果能外推到桌面操作、车辆或任意 VLA。

`CLAIM-18-04`（recommendation）：长时 VLA 应分别评测 subgoal selection、phase completion、memory correctness、recovery、动作闭环和全任务 outcome；增加 context/chunk 长度不能替代显式进度证据与 replanning。

## 18.7 World-Action Model：按接口分，不按名字分

截至核查日，WAM 仍是研究趋势标签而非统一标准。[World Models to World Action Models 教程与资源库](https://github.com/clearlab-sustech/WorldModelSurvey)给出一组有用分类，本书将其改写为可审计接口：

| 路径 | 训练/推理接口 | 是否天然可 rollout | 关键检查 |
| --- | --- | --- | --- |
| imagine-then-execute | 先生成未来，再由 inverse/goal policy 产动作 | 取决于未来是否动作条件化 | future 可达性、逆动力学歧义 |
| video-feature-conditioned action | 未来模型特征条件化 action head | 不一定 | 特征是否真的携带动作后果 |
| joint video-action modeling | 同一模型联合生成未来与动作 | 不一定可交互递归 | 因果 mask、动作条件性、时间对齐 |
| auxiliary future prediction | future loss 只在训练期塑造 policy | 通常不提供 | 去掉 future head 后的因果 ablation |

*TAB-18-03：World-Action Model 的四类实现路径。联合预测不自动得到 planner、critic 或 simulator。*

[SimWAM 作者仓库](https://github.com/H-EmbodVis/SimWAM)是自动驾驶中的第四类案例：视频生成作为训练信号，推理走 action-only 路径，并公开 NAVSIM 上的 supervised/action-only RL 代码入口 `[O,R1]`。这恰好说明 WAM 可以在部署时不生成未来；此时不能仅凭名称声称它提供在线 world rollout。

`CLAIM-18-05`（inference）：一个 WAM 是否能用于规划、RL simulator 或安全反事实，取决于它是否暴露经验证的动作条件未来、递归 state、reward/termination 与候选比较接口；联合视频—动作 loss 或“world”命名本身不提供这些能力。

## 18.8 自动驾驶正文：后训练必须保留独立道路真值

自动驾驶 SFT 数据常偏向正常行驶；后训练可以提高稀有 cut-in、施工改道、急刹、遮挡行人和传感器故障的覆盖。交互来源可选第19章默认 MetaDrive、需要多相机高保真时的 CARLA、冻结日志的 counterfactual，或 learned video/latent model；四者的真实性等级不能混写。

reward 应拆出路线完成、碰撞、道路边界、规则、舒适、干预和最小风险状态。碰撞/越界属于硬 gate，不应仅作为可被路线进度抵消的负 reward。episode-level “到达终点”会像 `EXP-18-01` 一样压低失败轨迹中的正确避险和恢复动作，需要 phase/progress 与事件级标注。

[WorldRFT](https://arxiv.org/abs/2512.19133)是 latent world model、分层规划和 reinforcement fine-tuning 的驾驶案例 `[A,R0]`；[SimWAM](https://github.com/H-EmbodVis/SimWAM)则代表 future-prediction auxiliary + action-only inference。两者都只能作为架构证据，不能把上游 nuScenes/NAVSIM 数字当作本书或道路部署结果。

`CLAIM-18-06`（recommendation）：驾驶 policy 的后训练更新必须在未用于 policy/world-model/reward 训练的闭环路线和 seed 上复核碰撞、路线、干预、规则、舒适与尾部风险，并通过第21章执行网关；learned simulator reward 或 open-loop score 不能授权车辆控制。

## 18.9 资源、开源与许可路线

| 档位 | 路径 | 当前状态 | 上限与停止条件 |
| --- | --- | --- | --- |
| S | 四轨迹离线重加权 fixture | 已运行 | 标准库、CPU、零下载 |
| M | 冻结 LIBERO 小子集做离线权重/critic 接口 | 可选、待运行 | Docker；先审计数据与磁盘，不训练大 VLA |
| L1 | 小 policy/adapter 的短步后训练 | 可选、待验证 | 目标 24 GB 单卡；先测峰值 VRAM、墙钟和外部 return |
| L2 | learned-world-model + VLA 对照 | 非必需、待验证 | 最多 2×80 GB；超限则只做论文/接口审计 |

当前无 GPU，M/L1/L2 均未运行。RIPT-VLA 作者仓库的 OpenVLA-OFT 示例建议至少 3 GPU，超出本书最多双卡的默认范围，因此不能直接成为核心复现；只有经实测缩小且不削弱比较合同的配方才能进入 L1/L2。World-Gymnast、VLA-RFT、WoVR 的 world model + policy 完整栈也未证明落入 24 GB 单卡。

本章不要求购买硬件。S 档原创代码、数据和图表为 MIT；RIPT-VLA、World-Gymnast、LIBERO、OpenVLA-OFT、world model、checkpoint 和生成数据各有独立许可与来源要求，运行前必须锁定 commit 和资产条款。

## 18.10 失效模式与停止条件

重点失败包括：reward 与任务错位、VLM verifier 被视觉伪迹欺骗、terminal/timeout 混淆、成功轨迹过采样导致 ESS/coverage 塌缩、失败中有用恢复被丢弃、critic 对 OOD action 过估计、policy 更新后离开 world-model support、长 chunk 无法中断、memory 写入错误阶段、subgoal 循环，以及模拟成功但独立环境退化。

出现以下任一情况就停止升级 policy：ESS 或分桶 coverage 低于预注册阈值；真实/独立仿真 return 与 model return 排序反转；碰撞/干预/安全尾部恶化；reward audit 发现捷径；action schema 或时间戳不匹配；结果无法追溯 policy、world model、reward 和 seed。

## 小结与练习

VLA 后训练的价值来自 outcome 和交互，风险也来自 outcome 定义与交互环境。离线重加权能移动 target，却可能缩小有效样本和恢复覆盖；world-model rollout 能降低真实交互成本，却给 policy 新增可利用的模型漏洞。长时能力需要层级、记忆、进度与恢复，WAM 则必须回到实际接口判断。

1. 给 fixture 增加一条“最终失败但第一阶段最优”的轨迹，比较 episode 与 step-level 权重。
2. 为全成功/全失败 rollout group 写 leave-one-out advantage 的退化测试。
3. 给一个五阶段操作任务定义 subgoal completion、stuck 和 recovery 状态机。
4. 任选 WAM 项目，判断它属于 `TAB-18-03` 哪一行，并找出因果 ablation。
5. 为驾驶 cut-in 后训练写出 SFT、MetaDrive RL、learned simulator RL 和 held-out CARLA 四列对照。

## 延伸阅读

- Tan et al., [RIPT-VLA](https://arxiv.org/abs/2505.17016) 与[作者代码](https://github.com/Ariostgx/ript-vla)；
- Li et al., [VLA-RFT](https://arxiv.org/abs/2510.00406)；
- Sharma et al., [World-Gymnast](https://arxiv.org/abs/2602.02454) 与[作者代码](https://github.com/world-gymnast/world-gymnast)；
- Jiang et al., [WoVR](https://arxiv.org/abs/2602.13977)；
- Zhang et al., [From World Models to World Action Models](https://github.com/clearlab-sustech/WorldModelSurvey)；
- [SimWAM 作者仓库](https://github.com/H-EmbodVis/SimWAM)与 [WorldRFT](https://arxiv.org/abs/2512.19133)。

## 下一章接口与审查记录

第19章提供物理 simulator 与 sim-gap 锚点；第20章固定 policy 评测协议；第21章把更新后的 policy 放入时延、watchdog 和 fallback 边界。第22章将把这些合同收束成一个可审计综合项目。

- 内容审查：通过；
- 代码审查：通过；
- 一致性审查：通过；
- 教学审查：通过；
- 审查记录路径：`reviews/batch-d-review.md`；
- 已知限制：只有离线标量重加权，没有 VLA/RL/world-model 训练、LIBERO、物理仿真、GPU、机器人或车辆。
