# 读者术语表

本页是面向在线阅读的快速索引。它不替代各章推导；当一个词在不同论文里含义不完全一致时，这里采用本书的工作定义，并给出最适合回读的章节。作者侧的完整约束以 `specs/terminology.md` 为准。

## 先看清概念所在的层级

本书反复讨论的对象可以连成一条从世界到行动、再返回世界的链：

> 环境具有任务相关的真实状态；传感器只提供部分观测；模型把观测历史编码为表征，其中一部分可解释为对隐藏状态的信念；世界模型预测状态或观测怎样随动作演化；策略或规划器据此选择动作；动作改变环境，新的观测再进入下一轮决策。

这条链中的词不能按“越靠后越高级”理解。表征不一定是状态，预测模型不一定能规划，规划器不等于策略，能够输出动作也不意味着内部具有可调用的世界模型。判断一个系统时，应先问它位于链条的哪一层、输入输出是什么，再讨论模型名称。

## 闭环与决策

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| 环境（environment） | 接收动作并产生后续状态与观测的系统 | 不只指仿真器 | [第1章](part-01-loop/ch01-from-seeing-to-acting.md) |
| 状态（state） | 足以描述任务相关环境条件的变量 | 不等于原始像素或单帧特征 | [第2章](part-01-loop/ch02-what-is-a-world-model.md) |
| 观测（observation） | 传感器在某时刻提供的数据 | 不等于完整真实状态 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 信念状态（belief state） | 根据历史对不可完全观测状态形成的任务相关估计 | 不等于任意 latent | [第6章](part-02-world-models/ch06-rssm.md) |
| 动作（action） | 施加到环境或下层控制器的决策量 | 文本计划只有经过 grounding 才是可执行动作 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 策略（policy） | 从观测、状态或信念映射到动作分布的规则 | 不等于世界模型 | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| 规划器（planner） | 在给定目标、模型与约束下比较候选动作或轨迹并作出选择的决策组件 | 不等于提供未来预测的世界模型；也不必是一次前向的策略 | [第7章](part-02-world-models/ch07-model-based-planning.md) |
| rollout | 从初始条件连续推进环境或模型得到的轨迹 | 不等于单次前向 | [第7章](part-02-world-models/ch07-model-based-planning.md) |
| 模型预测控制（MPC） | 在有限时域内用模型优化动作序列，执行部分动作后根据新观测再次规划 | 不是一次生成整段动作并盲执行；重规划也不能修复错误模型 | [第7章](part-02-world-models/ch07-model-based-planning.md) |
| 交叉熵方法（CEM） | 反复采样候选、保留高分 elite 并更新采样分布的近似优化器 | 名称中的“交叉熵”不表示它是分类损失，也不保证找到全局最优 | [第7章](part-02-world-models/ch07-model-based-planning.md) |
| 开环评测（open-loop） | 模型输出不会持续改变后续输入的评测 | 离线数据不必然意味着评测逻辑是开环 | [第4章](part-01-loop/ch04-data-and-protocols.md) |
| 闭环评测（closed-loop） | 动作改变环境，后续观测再反馈给策略 | 不等于单步动作准确率 | [第9章](part-02-world-models/ch09-evaluation.md) |
| 反事实（counterfactual） | 固定历史及其余条件，只改变指定干预变量所得的替代未来 | 不等于任意随机生成的另一未来 | [第11章](part-03-representations/ch11-action-conditioned-video.md) |
| terminated | episode 因任务定义内的自然终态结束；常见价值目标在此关闭 bootstrap | 不等于外部日志截断 | [第4章](part-01-loop/ch04-data-and-protocols.md) |
| truncated | episode 因任务外部采集/时间限制结束；最终观测有效时通常仍可 bootstrap | 不等于任务成功或失败 | [第4章](part-01-loop/ch04-data-and-protocols.md) |
| sensor validity mask | 逐样本显式说明传感器值是否存在且可用 | 缺字段、零图或复制上一帧不等于 mask | [第4章](part-01-loop/ch04-data-and-protocols.md) |
| sensor skew | 传感器来源时间戳相对冻结参考时间的偏差 | 容差内不等于物理同时曝光 | [第4章](part-01-loop/ch04-data-and-protocols.md) |

## 模型、表示与仿真

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| 世界模型（world model） | 对任务相关状态及其随动作演化规律的可学习表示 | 不是任意视频生成器 | [第2章](part-01-loop/ch02-what-is-a-world-model.md) |
| 表征（representation） | 模型从观测或历史中提取、编码并提供给下游使用的信息 | 可读出某个变量不等于它是完整状态，也不证明策略会使用它 | [第10章](part-03-representations/ch10-jepa-representations.md) |
| 潜在状态（latent state） | 模型内部用于递推、预测或决策的隐变量 | 不自动等于真实环境状态或经过校准的信念状态 | [第6章](part-02-world-models/ch06-rssm.md) |
| 转移模型（transition model） | 预测状态在动作条件下如何变化 | 不等于无动作条件编码器 | [第6章](part-02-world-models/ch06-rssm.md) |
| 循环状态空间模型（RSSM） | 用循环确定性状态汇总历史，并以随机潜变量表达观测修正与不确定性的状态空间模型族 | RSSM 的 prior/posterior 数据流较稳定，潜变量形式和损失实现并不唯一 | [第6章](part-02-world-models/ch06-rssm.md) |
| 逆动力学模型（IDM） | 根据相邻状态、观测或表征推断可能动作的模型 | 转移到动作可能一对多；额外 IDM 会改变方法的归因与比较成本 | [第9章](part-02-world-models/ch09-evaluation.md) |
| renderer | 从给定状态、场景或描述生成传感器外观 | 不自动含交互规则或状态转移 | [第11章](part-03-representations/ch11-action-conditioned-video.md) |
| 仿真器（simulator） | 用显式规则、数值方法或学习模型推进环境 | 与世界模型可以重叠，但不是同义词 | [第19章](part-06-systems/ch19-physical-simulation-and-sim2real.md) |
| learned simulator | 根据动作推进学习状态，并向交互方提供后续观测 | 不是只生成一次无反馈视频 | [第17章](part-05-fusion/ch17-world-model-policy-utility.md) |
| 模型利用（model exploitation） | 规划器主动选择模型错误预测为高回报的区域 | 不只是通常意义的训练过拟合 | [第9章](part-02-world-models/ch09-evaluation.md) |
| aleatoric 不确定性 | 给定完整任务条件后仍存在的结果随机性或多模态性 | 不等于模型不知道 | [第5章](part-02-world-models/ch05-generative-foundations.md) |
| epistemic 不确定性 | 数据覆盖、参数或模型知识不足造成的不确定性 | 单个模型重复采样不会自动暴露它 | [第5章](part-02-world-models/ch05-generative-foundations.md) |
| 分布外（OOD） | 相对明确的训练、校准或参考分布，输入、状态或动作落在其覆盖之外 | 不是“看起来奇怪”的同义词；OOD 分数也不自动等于失败概率 | [第9章](part-02-world-models/ch09-evaluation.md) |
| selective coverage / risk | 拒绝阈值下被接受的样本比例 / 只在接受样本上计算的风险 | 不等于置信区间 coverage；零接受时 risk 未定义 | [第9章](part-02-world-models/ch09-evaluation.md) |
| risk–coverage curve | 扫描冻结不确定性阈值得到的 coverage 与接受样本风险关系 | 不等于单个 AUROC 或拒绝率 | [第21章](part-06-systems/ch21-deployment-realtime-and-safety.md) |
| JEPA | 从上下文预测目标区域表示的联合嵌入预测架构族 | 不等于所有无像素解码器的编码器 | [第10章](part-03-representations/ch10-jepa-representations.md) |
| probe | 在冻结或受限表征上训练的诊断读出器 | probe 成功不证明策略会使用该信息 | [第10章](part-03-representations/ch10-jepa-representations.md) |
| Sim2Real | 从仿真训练或验证迁移到真实系统的过程 | 仿真高分不是实机高分的保证 | [第19章](part-06-systems/ch19-physical-simulation-and-sim2real.md) |

## 空间与几何

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| frame / 坐标系 | 规定原点、轴向、手系与单位的参考框架 | 相同 shape 不代表相同几何语义 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| image/video frame | 图像或视频序列中的一帧采样 | 不等于 coordinate frame；应结合时间戳理解 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 相机内参（intrinsics） | 把相机坐标与像素连接的焦距、主点及相机模型参数 | 不描述相机相对机器人放在哪里 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 外参（extrinsics） | 两个坐标系之间的刚体变换 | 必须声明变换方向和时刻，不只是一个 `4×4` 数组 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| proper rotation | 满足 `RᵀR=I` 且 `det(R)=+1` 的旋转矩阵 | 缩放、剪切和镜像不能当作刚体旋转 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| optical frame | 常见相机光学轴约定：x 右、y 下、z 前；实际接口仍需查文档 | 不能默认等同机器人 body frame | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| z-depth / ray range | z-depth 是光轴坐标，range 是沿成像射线的欧氏距离 | 二者只在主点射线上相同 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 位姿（pose） | 刚体相对指定 frame 的位置与朝向 | 不只是位置坐标 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 点云（point cloud） | 一组带 frame 与单位的三维采样点，通常表示已观测表面 | 没有点不等于空间已知为空 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 体素（voxel） | 三维网格中的一个体积单元 | 必须同时给范围、原点和分辨率 | [第12章](part-03-representations/ch12-actionable-space.md) |
| BEV | 把空间投影或聚合到鸟瞰平面的表示 | 不自动保留完整高度、遮挡与碰撞关系 | [第12章](part-03-representations/ch12-actionable-space.md) |
| occupancy | 空间位置被占用的概率或状态 | 不只用于 3D 重建 | [第12章](part-03-representations/ch12-actionable-space.md) |
| 三态 occupancy | 把证据分为 `free`、`occupied`、`unknown` | 未检测或视野外不能默认是 free | [第12章](part-03-representations/ch12-actionable-space.md) |
| affordance | 环境或对象对指定本体与动作提供的可行动性 | 不等于对象类别 | [第12章](part-03-representations/ch12-actionable-space.md) |

## 策略与动作接口

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| 行为克隆（behavior cloning） | 在专家数据上监督学习动作 | 开环拟合好不保证闭环成功 | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| DAgger | 让当前策略访问状态，由专家标注并聚合回训练集的交互式模仿学习 | 离线加扰动数据不能自动称为 DAgger | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| action chunk | 一次联合预测的未来动作序列 | prediction horizon 不等于实际盲执行长度 | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| prediction horizon | 策略一次预测的未来动作长度 | 不等于控制频率或 execution horizon | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| execution horizon | 一个预测块实际执行多少步后重新规划 | 不一定执行完整预测块 | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| Diffusion Policy | 在观测条件下通过去噪过程采样动作或动作块的策略族 | 不等于任意含噪训练 | [第14章](part-04-policies/ch14-generative-actions.md) |
| Flow Matching | 回归条件向量场以连接 base 与目标分布的方法 | 不自动等于一步生成 | [第14章](part-04-policies/ch14-generative-actions.md) |
| 视觉语言模型（VLM） | 以视觉与语言为主要输入、产生文本或结构化语义输出的模型族 | 未经动作训练、grounding 和闭环验证的 VLM 不是 VLA | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| VLA | 将视觉、语言和机器人状态映射为动作的策略架构族 | 不自动具有世界模型 | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| action schema | 规定字段、顺序、frame、单位、频率、horizon、范围和版本的动作合同 | 不只是 tensor shape | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| action grounding | 把语义输出映射成指定本体可执行动作 | 可解析文本不代表动力学可执行 | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| canonical action | 为跨数据或本体对齐定义的版本化中间动作语义 | 不是所有本体都能直接执行的万能动作 | [第16章](part-04-policies/ch16-data-scaling-and-adaptation.md) |
| 有效样本量（ESS） | 对非负权重常用 $(\sum_i w_i)^2/\sum_i w_i^2$ 衡量权重集中程度 | 必须说明样本单位；trajectory 级 ESS 不能解释为 transition 或 token 数 | [第18章](part-05-fusion/ch18-vla-post-training-and-wam.md) |
| REINFORCE Leave-One-Out（RLOO） | 用同组其他 rollout 的平均 reward 作为当前样本 baseline 的相对优势估计 | 全组 reward 相同时信号退化；重采样会改变实际任务分布 | [第18章](part-05-fusion/ch18-vla-post-training-and-wam.md) |
| Real-Time Chunking（RTC） | 后台持续生成并按时间对齐、融合动作块的在线执行方式 | 减少阻塞不等于动作新鲜；仍需监控队列、观测年龄与 deadline | [第21章](part-06-systems/ch21-deployment-realtime-and-safety.md) |

## 常用优化量与评测指标

| 缩写/术语 | 回答的问题 | 不能单独证明 | 首读章节 |
| --- | --- | --- | --- |
| KL divergence | 一个概率分布相对另一个分布的有向差异；RSSM 中还必须结合 stop-gradient 与阈值看更新路径 | 分布之间的任务效用、对称距离或梯度实际流向 | [第6章](part-02-world-models/ch06-rssm.md) |
| 负对数似然（NLL） | 模型给已观测样本分配了多少概率质量 | 样本视觉质量、mode coverage、连续变量下跨表示的公平比较 | [第5章](part-02-world-models/ch05-generative-foundations.md) |
| MAE / RMSE | 逐元素绝对误差 / 均方根误差；RMSE 对大误差更敏感 | 时序因果、动作语义、闭环成功或安全后果 | [第1章](part-01-loop/ch01-from-seeing-to-acting.md) |
| IoU | 两个区域交集与并集之比，常用于检测、分割或 occupancy | 未观测空间语义、几何可达性或闭环效用 | [第12章](part-03-representations/ch12-actionable-space.md) |
| LPIPS | 在特征空间比较两幅图像的感知距离 | 物理一致性、动作条件正确或控制效用 | [第9章](part-02-world-models/ch09-evaluation.md) |
| FVD | 比较两组视频在固定特征空间中的分布差异 | 单条视频正确、因果动力学、规划排序或闭环安全 | [第9章](part-02-world-models/ch09-evaluation.md) |

## 证据、资源与安全

| 标记/术语 | 含义 |
| --- | --- |
| `CLAIM-*` | 维护层连接正文结论与 manifest、来源或结果的隐藏证据索引；不在读者正文显示，也不要求读者记忆 |
| `[P]` / `[A]` | 已同行评审论文 / 预印本或技术报告；表示来源类型，不表示本书复现 |
| `[O]` | 官方文档、官方仓库或官方项目页 |
| `R0`～`R4` | 从“只读来源”到“完整复现/扩展”的递进复现状态；具体门槛见[第4章](part-01-loop/ch04-data-and-protocols.md) |
| `S` | 概念与接口证据：零下载或极小 CPU fixture，用于暴露反例、算术和合同边界；不是目标模型成绩，也不是阅读正文的门槛 |
| `M` | 轻量外部证据：小型数据、规则环境或物理仿真中的基线与接口检查；先核验许可、体积、分母和独立评测，不默认要求训练大模型 |
| `L1` | 受限学习实验：目标不超过 24 GB 单卡，必须实测资源、时延和外部效度；只有 M 档无法回答核心问题时才升级 |
| `L2` | 高成本可选扩展：最高不超过 2×80 GB，并需独立授权与停止条件；不是章节完成、读完全书或接受概念结论的前提 |
| benchmark card | 在运行前冻结用途、系统、数据划分、协议、指标、统计、声明边界和报告要求的评测合同；单次运行与测量值分别进入 experiment card 和 result，见[第9章](part-02-world-models/ch09-evaluation.md)与[第20章](part-06-systems/ch20-embodied-evaluation.md) |
| 最小风险动作（MRM） | 系统异常时进入受约束安全状态的动作或流程；不是学习策略的普通输出，见[第21章](part-06-systems/ch21-deployment-realtime-and-safety.md) |

## 常见缩写速查

| 缩写 | 英文全称 | 本书中的中文含义 |
| --- | --- | --- |
| CV | Computer Vision | 计算机视觉 |
| MDP | Markov Decision Process | 马尔可夫决策过程 |
| POMDP | Partially Observable Markov Decision Process | 部分可观测马尔可夫决策过程 |
| VAE | Variational Autoencoder | 变分自编码器 |
| VQ-VAE | Vector-Quantized Variational Autoencoder | 向量量化变分自编码器 |
| RSSM | Recurrent State-Space Model | 循环状态空间模型 |
| MPC | Model Predictive Control | 模型预测控制 |
| CEM | Cross-Entropy Method | 交叉熵方法 |
| JEPA | Joint-Embedding Predictive Architecture | 联合嵌入预测架构 |
| BEV | Bird's-Eye View | 鸟瞰图或鸟瞰表示 |
| OOD | Out of Distribution | 分布外 |
| BC | Behavior Cloning | 行为克隆 |
| ACT | Action Chunking with Transformers | 基于 Transformer 的动作分块方法 |
| VLM | Vision-Language Model | 视觉语言模型 |
| VLA | Vision-Language-Action | 视觉-语言-动作模型或策略 |
| SFT | Supervised Fine-Tuning | 监督微调 |
| WAM | World-Action Model | 世界-动作模型；尚无统一能力定义 |
| ESS | Effective Sample Size | 有效样本量 |
| RTC | Real-Time Chunking | 实时动作分块 |
| MRM | Minimum Risk Maneuver | 最小风险动作或最小风险机动 |

## 查词时的三个检查

1. 这个词描述的是观测、内部表示、环境状态，还是动作接口？
2. 结论来自论文/官方资料、本书 CPU fixture，还是尚待运行的 GPU/仿真实验？
3. 数字是否同时给出了协议、分母、资源、版本和限制？

若答案不清楚，应回到相应章节的“本章契约”“结果、资源与边界”和实验卡，而不是依赖术语名称自行推断。
