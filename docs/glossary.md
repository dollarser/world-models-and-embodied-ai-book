# 读者术语表

本页是面向在线阅读的快速索引。它不替代各章推导；当一个词在不同论文里含义不完全一致时，这里采用本书的工作定义，并给出最适合回读的章节。作者侧的完整约束以 `specs/terminology.md` 为准。

## 闭环与决策

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| 环境（environment） | 接收动作并产生后续状态与观测的系统 | 不只指仿真器 | [第1章](part-01-loop/ch01-from-seeing-to-acting.md) |
| 状态（state） | 足以描述任务相关环境条件的变量 | 不等于原始像素或单帧特征 | [第2章](part-01-loop/ch02-what-is-a-world-model.md) |
| 观测（observation） | 传感器在某时刻提供的数据 | 不等于完整真实状态 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 信念状态（belief state） | 根据历史对不可完全观测状态形成的任务相关估计 | 不等于任意 latent | [第6章](part-02-world-models/ch06-rssm.md) |
| 动作（action） | 施加到环境或下层控制器的决策量 | 文本计划只有经过 grounding 才是可执行动作 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 策略（policy） | 从观测、状态或信念映射到动作分布的规则 | 不等于世界模型 | [第13章](part-04-policies/ch13-imitation-and-action-chunks.md) |
| rollout | 从初始条件连续推进环境或模型得到的轨迹 | 不等于单次前向 | [第7章](part-02-world-models/ch07-model-based-planning.md) |
| 开环评测（open-loop） | 模型输出不会持续改变后续输入的评测 | 离线数据不必然意味着评测逻辑是开环 | [第4章](part-01-loop/ch04-data-and-protocols.md) |
| 闭环评测（closed-loop） | 动作改变环境，后续观测再反馈给策略 | 不等于单步动作准确率 | [第9章](part-02-world-models/ch09-evaluation.md) |
| 反事实（counterfactual） | 固定历史及其余条件，只改变指定干预变量所得的替代未来 | 不等于任意随机生成的另一未来 | [第11章](part-03-representations/ch11-action-conditioned-video.md) |

## 模型、表示与仿真

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| 世界模型（world model） | 对任务相关状态及其随动作演化规律的可学习表示 | 不是任意视频生成器 | [第2章](part-01-loop/ch02-what-is-a-world-model.md) |
| 转移模型（transition model） | 预测状态在动作条件下如何变化 | 不等于无动作条件编码器 | [第6章](part-02-world-models/ch06-rssm.md) |
| renderer | 从给定状态、场景或描述生成传感器外观 | 不自动含交互规则或状态转移 | [第11章](part-03-representations/ch11-action-conditioned-video.md) |
| 仿真器（simulator） | 用显式规则、数值方法或学习模型推进环境 | 与世界模型可以重叠，但不是同义词 | [第19章](part-06-systems/ch19-physical-simulation-and-sim2real.md) |
| learned simulator | 根据动作推进学习状态，并向交互方提供后续观测 | 不是只生成一次无反馈视频 | [第17章](part-05-fusion/ch17-world-model-policy-utility.md) |
| 模型利用（model exploitation） | 规划器主动选择模型错误预测为高回报的区域 | 不只是通常意义的训练过拟合 | [第9章](part-02-world-models/ch09-evaluation.md) |
| aleatoric 不确定性 | 给定完整任务条件后仍存在的结果随机性或多模态性 | 不等于模型不知道 | [第5章](part-02-world-models/ch05-generative-foundations.md) |
| epistemic 不确定性 | 数据覆盖、参数或模型知识不足造成的不确定性 | 单个模型重复采样不会自动暴露它 | [第5章](part-02-world-models/ch05-generative-foundations.md) |
| JEPA | 从上下文预测目标区域表示的联合嵌入预测架构族 | 不等于所有无像素解码器的编码器 | [第10章](part-03-representations/ch10-jepa-representations.md) |
| probe | 在冻结或受限表征上训练的诊断读出器 | probe 成功不证明策略会使用该信息 | [第10章](part-03-representations/ch10-jepa-representations.md) |
| Sim2Real | 从仿真训练或验证迁移到真实系统的过程 | 仿真高分不是实机高分的保证 | [第19章](part-06-systems/ch19-physical-simulation-and-sim2real.md) |

## 空间与几何

| 术语 | 本书中的含义 | 容易混淆之处 | 首读章节 |
| --- | --- | --- | --- |
| frame / 坐标系 | 规定原点、轴向、手系与单位的参考框架 | 相同 shape 不代表相同几何语义 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
| 位姿（pose） | 刚体相对指定 frame 的位置与朝向 | 不只是位置坐标 | [第3章](part-01-loop/ch03-minimal-robotics-and-decision.md) |
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
| VLA | 将视觉、语言和机器人状态映射为动作的策略架构族 | 不自动具有世界模型 | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| action schema | 规定字段、顺序、frame、单位、频率、horizon、范围和版本的动作合同 | 不只是 tensor shape | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| action grounding | 把语义输出映射成指定本体可执行动作 | 可解析文本不代表动力学可执行 | [第15章](part-04-policies/ch15-vla-architecture-patterns.md) |
| canonical action | 为跨数据或本体对齐定义的版本化中间动作语义 | 不是所有本体都能直接执行的万能动作 | [第16章](part-04-policies/ch16-data-scaling-and-adaptation.md) |

## 证据、资源与安全

| 标记/术语 | 含义 |
| --- | --- |
| `[P]` / `[A]` | 已同行评审论文 / 预印本或技术报告；表示来源类型，不表示本书复现 |
| `[O]` | 官方文档、官方仓库或官方项目页 |
| `R0`～`R4` | 从“只读来源”到“完整复现/扩展”的递进复现状态；具体门槛见[第4章](part-01-loop/ch04-data-and-protocols.md) |
| `S` | 零下载或极小 CPU fixture，当前无 GPU 设备也可完成 |
| `M` | 默认训练路径，设计目标不超过 24 GB 单卡 |
| `L1` / `L2` | 可选扩展；最高路径不超过 2×80 GB，且不是读完全书的前提 |
| benchmark card | 记录系统、任务、协议、指标、资源、失败样本和许可的结果合同，见[第20章](part-06-systems/ch20-embodied-evaluation.md) |
| 最小风险动作（MRM） | 系统异常时进入受约束安全状态的动作或流程；不是学习策略的普通输出，见[第21章](part-06-systems/ch21-deployment-realtime-and-safety.md) |

## 查词时的三个检查

1. 这个词描述的是观测、内部表示、环境状态，还是动作接口？
2. 结论来自论文/官方资料、本书 CPU fixture，还是尚待运行的 GPU/仿真实验？
3. 数字是否同时给出了协议、分母、资源、版本和限制？

若答案不清楚，应回到相应章节的“本章契约”“结果、资源与边界”和实验卡，而不是依赖术语名称自行推断。
