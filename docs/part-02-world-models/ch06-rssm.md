# 第6章 World Models 与循环状态空间模型

> 状态：`reviewed`
> 资料核查日期：2026-09-01
> 关联实验：`EXP-06-01`
> 关联声明：`CLAIM-06-01`～`CLAIM-06-06`
> 关联图表：`FIG-06-01` / `TAB-06-01` / `TAB-06-02`
> 资源档位：S / M / L1
> 当前验证：标准库 CPU smoke；完整训练与 GPU 资源待验证

## 本章契约

### 核心问题

当环境只能通过图像等不完整观测被看到时，模型应该记住什么，才能预测动作之后会发生什么？

### 先修知识

- 已具备：基本的编码器、循环网络和概率分布直觉；
- 本章补齐：部分可观测性、状态空间模型、prior/posterior 与 imagined rollout；
- 不要求：强化学习推导、控制理论或完整变分推断课程。

### 非目标

- 不在本章完整复现 PlaNet、DreamerV3 或论文规模分数；
- 不把“能重建画面”当成“状态足以支持决策”；
- 不在当前无 GPU 设备上推断 24GB 单卡训练成本。

### 学完后的可验证产出

读者应能：

1. 解释为什么单帧编码不足以表示部分可观测环境；
2. 区分确定性循环状态、随机潜变量、prior 和 posterior；
3. 画出训练时观测更新与想象 rollout 的两条数据流；
4. 用多步误差说明 one-step 准确不保证长时预测可靠；
5. 指出 CPU smoke、最小训练和论文复现之间的证据差异。

## 6.1 从“识别一帧”到“维护一个信念”

在图像分类里，一张图通常被当作完整输入。模型回答“这是什么”，但不必记住画面之外发生过什么。闭环控制不同：一帧图像可能看不到速度、遮挡后的物体、刚刚发生的接触，甚至无法判断摄像头与物体谁在运动。

考虑两张完全相同的桌面图像。第一种情况下，球静止在桌上；第二种情况下，球正高速向桌边滚动。当前像素可以相同，正确动作却不同。模型需要把历史观测和动作压缩成一个**信念状态**，而不是把当前帧直接当作环境状态。

早期 [World Models](https://arxiv.org/abs/1803.10122) 展示了“视觉编码器 + 循环动力学 + 控制器”的清晰分工：先压缩空间信息，再学习时间演化，最后让策略使用模型表示。它证明了在学习模型内部训练策略再迁回环境这一思路的可行性，但这种分解并没有自动解决长时误差和部分可观测性。

## 6.2 状态空间模型在解决什么

[PlaNet 的 ICML 论文](https://proceedings.mlr.press/v97/hafner19a.html)给出本章采用的代表性学习状态空间接口：观测背后存在更紧凑的潜在状态，模型一方面根据上一状态和动作预测下一状态，另一方面用新观测修正自己的信念。

可以把它写成两步：

\[
\text{prior:}\quad p_\theta(z_t \mid z_{t-1}, a_{t-1})
\]

\[
\text{posterior:}\quad q_\phi(z_t \mid z_{t-1}, a_{t-1}, o_t)
\]

prior 回答“如果只知道过去和动作，我预期现在是什么状态”；posterior 回答“看到新观测以后，我应该怎样修正这个预期”。训练阶段通常两者都存在；真正向未来想象时没有未来观测，只能连续使用 prior。

`CLAIM-06-01`（fact）：RSSM 的 prior 只使用历史状态和动作推进信念，posterior 在此基础上额外使用当前观测进行修正；两者承担的证据角色不同。

这一区别非常重要：模型可能在每一步都依靠新观测纠错，因此 one-step 指标很好；一旦拿走观测做十步 rollout，误差就开始复合。后续章节讨论模型规划和 Dreamer 时，会反复回到这条边界。

## 6.3 RSSM：为什么同时保留确定性和随机状态

[PlaNet](https://arxiv.org/abs/1811.04551) 使用同时包含确定性与随机转移成分的潜在动力学模型，并在潜在空间执行在线规划。RSSM（Recurrent State-Space Model）通常把内部状态拆成：

- `h_t`：确定性循环状态，负责累积可预测的历史和长时记忆；
- `s_t`：随机潜变量，表达当前状态的不确定性和多种可能未来。

一个简化的数据流是：

```mermaid
flowchart LR
    accTitle: FIG-06-01 RSSM 的 prior 与 posterior 数据流
    accDescr: 上一循环状态、随机状态和动作产生当前循环状态及 prior；训练时观测编码器形成 posterior，未来想象时只能沿 prior 推进。
    H0[上一循环状态 h_t-1] --> T[确定性转移]
    S0[上一随机状态 s_t-1] --> T
    A[动作 a_t-1] --> T
    T --> H1[循环状态 h_t]
    H1 --> P[prior p s_t given h_t]
    O[观测 o_t] --> E[观测编码器]
    E --> Q[posterior q s_t given h_t o_t]
    H1 --> Q
    P --> KL[一致性约束]
    Q --> KL
    Q --> D[观测/奖励/终止预测]
```

*FIG-06-01：教学版 RSSM 的 prior/posterior 数据流。训练阶段可以使用观测形成 posterior，未来想象阶段只能沿 prior 推进。来源：本书原创，MIT，2026-08-31。*

确定性状态并不意味着环境确定；随机状态也不等于简单地给网络加噪声。二者分工的动机是：循环路径保留跨时间的信息，随机变量表示单一历史下仍无法消除的不确定性。

## 6.4 训练时的三项基本压力

一个教学版 RSSM 至少同时承受三类压力：

1. **重建或表征压力**：潜在状态要保留观测中与任务相关的信息；
2. **动力学压力**：只根据过去状态和动作得到的 prior，应接近看到当前观测后的 posterior；
3. **任务压力**：潜在状态要能预测奖励、终止或价值，而不只是像素。

常见目标可以概括为：

\[
\mathcal{L} = \mathcal{L}_{obs} + \mathcal{L}_{reward} + \mathcal{L}_{continue}
+ \beta D_{KL}\left(q_\phi(s_t \mid h_t,o_t)\;\|\;p_\theta(s_t \mid h_t)\right)
\]

这个式子不是说所有实现都必须重建像素。`L_obs` 也可以是特征预测或其他表征目标。真正要问的是：状态丢掉的信息是否会改变后续动作选择？如果模型生成的杯子纹理不够逼真但仍能正确预测可抓取区域，它可能对控制足够有用；反过来，画面很漂亮却漏掉速度或接触状态，规划就会失败。

### KL 数值相同，不代表梯度流向相同

上面的单项 KL 适合建立直觉，却隐藏了现代实现中的梯度路由。以 2026-09-01 核查的 [DreamerV3 官方 `rssm.py` 快照 `e3f0224`](https://github.com/danijar/dreamerv3/blob/e3f02248693a79dc8b0ebd62c93683888ddaccfe/dreamerv3/rssm.py) 为例，代码把同一个前向 KL 拆为两项：

\[
\mathcal{L}_{dyn}=\max\!\left(\tau,
D_{KL}\!\left(\operatorname{sg}(q)\,\|\,p\right)\right)
\]

\[
\mathcal{L}_{rep}=\max\!\left(\tau,
D_{KL}\!\left(q\,\|\,\operatorname{sg}(p)\right)\right)
\]

其中 `sg` 是 stop-gradient，`τ` 是 `free_nats`。两项的前向数值相同，但 `L_dyn` 让 prior/dynamics 追随冻结的 posterior，`L_rep` 让 posterior/encoder 追随冻结的 prior。该[同一 commit 的配置](https://github.com/danijar/dreamerv3/blob/e3f02248693a79dc8b0ebd62c93683888ddaccfe/dreamerv3/configs.yaml)把 `free_nats` 设为 1.0，并在总损失中给 dynamics 与 representation 项分别乘 1.0 和 0.1；这是特定源码快照的实现事实，不是 RSSM 定义，也不应外推到 PlaNet、DreamerV1/V2、未来 DreamerV3 commit 或其他复现。

`free_nats` 还容易被日志误读：`max(raw_KL, τ)` 会让阈值以下的报告值停在 `τ`，但该常数区的 KL 梯度为零（边界点除外）。因此“KL loss 显示为 1”不能单独证明 prior 与 posterior 仍在被该项拉近，必须同时查看 raw KL、阈值、权重和梯度路由。

`CLAIM-06-05`（fact）：DreamerV3 官方快照 `e3f0224` 的 dynamics/representation KL 在前向计算中数值相同，但 stop-gradient 使二者更新不同参数；`free_nats` 又使阈值以下的 KL 成为常数区。该结论只描述所锁实现，而不是所有 RSSM 或未来 commit 的必备形式。

## 6.5 训练数据流与想象数据流

训练时，posterior 可以持续看到真实观测：

```text
历史状态 + 动作 → prior → 结合新观测得到 posterior → 预测并计算损失
```

想象 rollout 时，未来观测不存在：

```text
当前 posterior → 动作 → prior → 动作 → prior → ...
```

因此，训练时表现最好的分支和部署时真正使用的分支并不完全相同。需要至少分别报告：

- posterior filtering 的 one-step 误差；
- 关闭未来观测后的 multi-step prior 误差；
- 奖励、终止和任务相关状态的误差；
- 用模型选择动作后得到的真实闭环回报。

只报告第一项，会掩盖模型在规划时真正暴露的问题。

`CLAIM-06-02`（recommendation）：用于规划或 imagined learning 的状态空间模型，至少应分别报告观测修正后的 filtering 误差和关闭未来观测后的 multi-step prior 误差。

## 6.6 从 PlaNet 到 Dreamer：同一个模型，不同的使用方式

PlaNet 学习潜在动力学后，用规划器在线搜索动作序列。随后 [Dreamer](https://arxiv.org/abs/1912.01603) 在学习到的潜在模型内展开 imagined trajectories，并通过这些轨迹学习行为。两者共享的核心不是某个特定网络层，而是“学习任务相关状态—在模型中预测动作后果—用预测改善决策”的闭环。

DreamerV2 进一步采用离散潜变量处理 Atari 等任务；DreamerV3 后来形成跨多类控制任务的统一配置，并于 2025 年发表于 *Nature*。这些进展属于第8章的重点。本章只建立它们共同依赖的状态与数据流，不把最新实现细节塞进 RSSM 的基本定义。

## 6.7 EXP-06-01：RSSM 数据流 CPU smoke

当前配套实验不是神经网络训练。它使用一个带位置、速度和观测噪声的一维程序化系统、一个教学版“预测—观测修正”状态更新器，以及二分类分布的解析 KL，验证五件事：

1. 动作参与 prior 更新；
2. posterior 使用新观测修正状态；
3. 拿走未来观测后，多步 prior 误差通常比持续观测修正更快累积。
4. stop-gradient 不改变 dynamics/representation KL 的前向数值；
5. `free_nats` 能区分阈值以下的常数区与阈值以上的失配。

本地命令：

```bash
make ch06-smoke-local
make ch06-test-local
```

Docker 优先命令：

```bash
make ch06-smoke
```

该 smoke 只依赖 Python 标准库，不下载数据或模型。输出包含 filtering、open-loop 和 persistence 三类 RMSE，以及两组 KL 诊断。它验证的是接口、前向算术和评测协议，不计算真实梯度，不证明 RSSM 已经学会环境，也不能升级为 PlaNet/Dreamer 复现结果。

本轮基线使用 seed 7 的 32 步程序化轨迹，宿主 Python 与 CPU Docker 输出一致：

`TAB-06-01`：`EXP-06-01` 固定程序化 fixture 的三类 RMSE；这些指标只用于验证数据流与评测接口。

| 指标 | RMSE | 解释 |
| --- | ---: | --- |
| filtering | 0.06084 | 每步使用观测修正后的状态误差 |
| open-loop | 0.33317 | 初始化后只使用 prior 的多步误差 |
| persistence | 0.70437 | 用上一观测预测下一状态的朴素基线 |

原始结果记录在 `results/ch06/EXP-06-01-smoke.json`。这些数字只属于 `EXP-06-01` 的固定教学 fixture，不与论文分数比较，也不用于声称学习方法优于其他模型。

同一协议已冻结为 `benchmarks/BENCH-06-01.json`：它把 31 个有效转移、seed 7、filtering/open-loop 的观测可见性、persistence 基线、三项指标实现和禁止声明写成机器可校验字段。`experiment-card.json` 继续记录本次运行的代码、资源和命令，结果 JSON 只保存测量值。三类文件分开后，改变 seed、horizon 或未来观测可见性就属于协议变更，不能仍以同一 benchmark 版本横向比较。

`CLAIM-06-03`（result）：在 `EXP-06-01` 的固定 32 步 fixture 上，open-loop RMSE 为 0.33317，高于持续观测修正的 filtering RMSE 0.06084。该结果不外推到神经 RSSM、PlaNet 或 Dreamer。

| posterior / prior | raw KL（nat） | `free_nats` 后的 dyn/rep 值 | 权重后总值 |
| --- | ---: | ---: | ---: |
| `(0.5,0.5)` / `(0.55,0.45)` | 0.005025 | 1.000000 / 1.000000 | 1.100000 |
| `(0.5,0.5)` / `(0.99,0.01)` | 1.614463 | 1.614463 / 1.614463 | 1.775909 |

*TAB-06-02：`EXP-06-01` 的解析 KL 阈值反例。权重采用核查日期下官方配置的 dyn=1.0、rep=0.1；数值不包含神经网络或自动微分。*

`CLAIM-06-06`（result）：`EXP-06-01` 中，小失配 raw KL 约为 0.005，在 `free_nats=1` 时进入常数区；大失配 raw KL 约为 1.614，超过阈值。该结果只验证阈值算术，梯度接收方由合同标签表达而非由本实验测量。

## 6.8 一个必须保留的反例

假设模型每一步都能看到真实观测，并把 90% 的新观测直接写入状态。它的 one-step 误差可能很低，但这主要证明观测修正有效。一旦规划器要求模型独立预测未来二十步，误差仍会迅速增长。

因此，“posterior 重建得好”不能推出“prior 可以支撑规划”。本章的最小实验刻意同时输出 filtering 与 open-loop 指标，就是为了阻止这种证据偷换。

## 6.9 失效模式

- **posterior collapse**：随机状态不携带有效信息，解码器主要依赖确定性路径；
- **KL 日志误读**：只看阈值后的 loss，无法判断 raw KL 是否低于 free-nats，也无法判断哪条梯度路径主导训练；
- **复合误差**：训练分布主要来自真实历史，想象轨迹逐步偏离该分布；
- **遗漏任务变量**：像素损失鼓励保存纹理，却忽略速度、接触或遮挡状态；
- **错误不确定性**：单一平均未来掩盖多种可能结果；
- **模型利用**：后续策略发现并利用模型不真实的高回报区域；
- **指标错位**：视觉预测更好，但规划回报更差。

这些问题不能只靠调低训练损失解决。第7章会让规划器直接使用模型，从而观察模型误差怎样改变动作；第9章再建立系统评测协议。

## 6.10 自动驾驶：相同画面，不同闭合速度

跟车场景可以直接说明单帧观测为何不是完整状态。两张图像中，前车的像素框可能大小相近：第一种情况两车同速，第二种情况自车正在快速接近前车。若只看当前框，模型可能给出相同表示；制动决策却应不同。

驾驶信念状态至少可能需要融合：历史图像、ego speed、yaw rate、方向盘/油门/制动、前车相对速度、遮挡对象的轨迹，以及地图和信号灯状态。动作也必须进入转移：制动会改变下一时刻的 ego motion 和未来观测，不能只把动作当作展示标签。

`CLAIM-06-04`（inference）：在自动驾驶中，单帧 RGB 无法唯一确定闭合速度、遮挡对象轨迹和车辆动态；将历史观测与车辆动作纳入信念状态，是预测制动和变道后果的必要建模步骤，但仍需第9章的闭环协议验证是否足够。

本章不要求安装驾驶仿真器。第19章才用 MetaDrive 做 S/M 档闭环决策实验，并将 CARLA 保留为 L2 高保真选做项。

## 6.11 结果、资源、数据与许可

| 类型 | 声明/结果 | 来源或实验 ID | 状态 | 限制 |
| --- | --- | --- | --- | --- |
| 外部方法 | RSSM 区分历史转移与观测修正 | PlaNet/Dreamer 系列论文 | `[P/A]` | 具体实现和目标函数不同 |
| 本书结果 | open-loop 误差高于 filtering；KL 阈值两侧算术 | `EXP-06-01` | CPU smoke | 手工状态更新器与解析分布，不是神经训练或梯度验证 |
| 未验证 | mini-RSSM 在目标任务上的收敛与资源 | 无 | pending | 当前无 GPU，尚未实现训练 |

S 档 smoke 使用 MIT 许可的程序化一维 fixture、Python 标准库和 CPU，下载量为 0。M 档未来实现小型 PyTorch RSSM，默认上限为 24 GB 单卡；L1 只用于经过资源审计的官方 debug 配置。当前不购置硬件，也不从 smoke 推断 GPU 显存、训练时间或收敛。

## 6.12 小结

RSSM 的关键不是“在 RNN 后面再加一个随机变量”，而是明确区分两种信息来源：历史和动作提供 prior，新观测提供 posterior 修正。训练时持续看到观测，想象时只能依赖 prior；这条分布差异决定了为什么 one-step 预测不能替代 multi-step 与闭环评测。

## 练习

1. **概念判断**：一个只接收过去图像、不接收动作的视频预测器是否满足本书的世界模型工作定义？给出条件化回答。
2. **代码实验**：调整 `observation_gain`，观察 filtering RMSE 和 open-loop RMSE 是否同步变化，并解释原因。
3. **梯度判断**：在不运行代码的情况下，分别说明 `KL(sg(q)‖p)` 与 `KL(q‖sg(p))` 会更新谁；为什么两个日志值可能完全相同？
4. **阈值分析**：将 `free_nats` 改为 0、0.5 和 2，画出 raw KL 到报告 loss 的分段函数，并标出常数区。
5. **反例设计**：构造一种画面预测误差下降但控制所需状态变差的情况。
6. **迁移分析**：在自动驾驶中，哪些变量可能无法从单帧 RGB 唯一确定？它们分别会影响哪类动作？

## 自检要点

先区分本章标准库 fixture 的可观察结果与神经 RSSM 的一般结论。数值答案只对固定 seed、固定动力学和当前代码成立。

<details>
<summary>SELF-CHECK-06-01：无动作视频预测器</summary>

按本书用于控制与决策的工作定义，它通常不满足：它学习的是 `p(o_{t+1:t+H}|o_{≤t})`，无法回答候选动作 `a` 改变后未来如何变化。若任务只是被动环境预测，或动作由观测历史唯一决定且不需要反事实规划，可以把它称为特定用途的预测模型，但必须禁止“支持动作规划”的声明。要升级为本书主线世界模型，至少需显式动作条件、时间对齐和 E2 action-intervention 检查。

</details>

<details>
<summary>SELF-CHECK-06-02：observation gain</summary>

在当前固定轨迹中，将 `observation_gain` 取 0、0.25、0.5、0.65、1，filtering RMSE 约为 0.0446、0.0451、0.0537、0.0608、0.0863，而 open-loop RMSE 始终约为 0.3332。后者只从初态反复调用 `prior`，所以不读取该 gain；前者每步用带噪观测修正 position，因而会变化且不保证 gain 越高越好。这里 gain=0 时 `velocity_gain=0.18` 仍会从 innovation 修正速度，不能把结果误读成“完全不使用观测”。

</details>

<details>
<summary>SELF-CHECK-06-03：KL 的梯度路由</summary>

`KL(sg(q)‖p)` 中 posterior `q` 被 stop-gradient，梯度只流向 dynamics prior `p`；`KL(q‖sg(p))` 中 prior 被截断，梯度只流向 representation/posterior `q`。两式前向都代入同一组概率值计算 `KL(q‖p)`，所以日志标量可以完全相同；stop-gradient 改的是反向图，不是前向数值。检查实现时应同时看 loss 数值、scale 与参数梯度目标。

</details>

<details>
<summary>SELF-CHECK-06-04：free nats 分段函数</summary>

当前 fixture 定义为 `L_c(k)=max(k,c)`，其中 raw KL `k≥0`、`c=free_nats`。当 `c=0` 时 `L=k`；`c=0.5` 时，`0≤k≤0.5` 为常数 0.5，之后为 `k`；`c=2` 时，`0≤k≤2` 为常数 2，之后为 `k`。这不是 `max(k-c,0)`：两种写法的数值、日志和 scale 不同。严格说拐点处两支相等；“常数区”可写为 `k<c`，并注明实现采用哪一侧的次梯度。

</details>

<details>
<summary>SELF-CHECK-06-05：像素更好、控制状态更差</summary>

例如驾驶视频中 99% 像素是静态道路与天空，模型通过增强背景纹理把 pixel MSE 降低，却把只占少量像素的刹车灯、横穿行人速度或遮挡后车辆存在概率平均掉。画面会更锐利，但 TTC、object permanence 或相对速度 latent 更差，导致制动时机错误。合格反例应同时给出视觉指标改善、决策变量退化和对应动作后果，而不是只说“像素不重要”。

</details>

<details>
<summary>SELF-CHECK-06-06：单帧 RGB 的不可辨识变量</summary>

单帧通常不能唯一确定相对速度/加速度、他车驾驶意图、遮挡物存在状态、交通灯相位变化方向、路面摩擦、ego 延迟与执行器状态。相对运动和意图影响跟车、变道与避让；灯相位影响停车/通过；摩擦影响制动距离和转向上限；执行器状态影响 action timing。需要时间序列、ego motion/control、地图或额外传感器形成 belief，并保留不确定性；多帧也不保证所有隐变量都可辨识。

</details>

## 延伸阅读

- Ha & Schmidhuber, [World Models](https://arxiv.org/abs/1803.10122)，`[A]`；
- Hafner et al., [Learning Latent Dynamics for Planning from Pixels](https://arxiv.org/abs/1811.04551)，PlaNet，`[A]`；
- Hafner et al., [Dream to Control](https://arxiv.org/abs/1912.01603)，`[A]`；
- Hafner et al., [Mastering Atari with Discrete World Models](https://arxiv.org/abs/2010.02193)，`[P]`；
- Hafner et al., [Mastering Diverse Control Tasks through World Models](https://www.nature.com/articles/s41586-025-08744-2)，DreamerV3，`[P]`；
- [DreamerV3 公开仓库](https://github.com/danijar/dreamerv3)，资产状态需在具体实验卡中记录。

## 下一章接口

第7章将固定一个已学习或程序化的动力学模型，用 CEM 等方法选择动作。届时，本章的 prior 不再只是预测工具，而会直接影响策略；任何被规划器利用的模型误差都会变成闭环失败。

## 验收与审查记录

```text
本地检查：make check-local
严格检查：make check
章节 smoke：make ch06-smoke
文档构建：make docs-build
```

- 内容审查：通过；
- 代码审查：通过；
- 一致性审查：通过；
- 教学审查：通过；
- 审查记录路径：`reviews/batch-a-review.md`、`reviews/part-02-exercise-self-check-review-2026-09-02.md`；
- 已知限制与下一步：PyTorch mini-RSSM、24 GB 单卡资源和完整训练仍待后续阶段验证。
