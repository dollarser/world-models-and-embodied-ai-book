# 第12章 可行动的空间表征

## 本章契约

### 核心问题

怎样把相机看到的像素变成能回答“哪里可走、哪里会碰、从哪里接近、物体正在往哪动”的空间状态？一幅看起来真实的三维重建，为什么不一定能直接用于机器人或自动驾驶？

### 先修知识

- 已具备：第3章的坐标系、针孔投影、深度、点云与鸟瞰图（Bird's-Eye View, BEV）最小桥接；第9章的任务指标与失败分析；
- 本章补齐：体素、三态 occupancy、语义与动态空间、场景关系和 affordance；
- 不要求：多视图几何、NeRF/3DGS 训练、点云网络、机器人硬件、驾驶数据或 GPU。

如果你没有 3D 视觉经验，可以直接阅读。本章从“一条深度射线提供了什么证据”开始；需要手算投影时再回看第3章即可。

第一次阅读只追踪五个问题即可：深度是 z-depth 还是 range；点当前在哪个 frame；变换方向与时刻是什么；栅格的原点/分辨率是什么；未观测区域怎样保留为 unknown。网络名称、稀疏数据结构和完整多视图推导可以后读。

### 非目标

- 不把漂亮 novel view 等同几何、碰撞或可行驶空间正确；
- 不把没观测到的空间默认标成自由；
- 不把对象类别等同它对某个本体、动作和时刻的 affordance；
- 不声称本书运行了 Occ3D/OpenScene、Nerfstudio 或 D4RT；
- 不用学习式 occupancy 绕过定位、碰撞检查或独立安全层。

### 学完后的可验证产出

读者应能把空间地图理解为带传感器与位姿条件的信念，从带 frame/单位/时间戳的 RGB-D 或点云构造简化 occupancy，解释 free/occupied/unknown 及其证据来源，分析分辨率、遮挡、坐标偏移、动态多未来和更新时效，拒绝只检查稀疏 waypoint 的路径假安全，并把空间状态连接到导航、接近、抓取或驾驶规划。

## 12.1 从像素到行动约束

RGB 告诉我们表面看起来怎样，深度把像素连接到尺度，标定把不同传感器和时刻放入共同坐标系。第3章已经给出反投影：像素 `(u,v)` 和深度 `d` 经过内参可得到相机坐标点，再由外参变换到机器人、车辆或世界 frame。本章关心接下来的压缩：哪些空间证据必须保留，才能支持动作？

```mermaid
flowchart TB
    accTitle: FIG-12-01 从传感器证据到可行动空间
    accDescr: RGB-D、激光雷达和多视图证据变换为带坐标系与时间的点，再压缩成体素或俯视表示、三态占用、语义速度和可行动区域供规划使用。
    S[RGB-D / lidar / 多视图] --> P[带 frame 与时间戳的点]
    P --> V[体素 / BEV / 对象与关系]
    V --> O[free / occupied / unknown]
    O --> D[语义、速度、置信度]
    D --> A[可行驶/可接近/可抓取区域]
    A --> C[规划、控制与独立安全检查]
```

*FIG-12-01：从传感器证据到可行动空间的最小链路。每次压缩都应保留 frame、时间与未知状态。来源：本书原创，CC BY-NC 4.0，2026-08-31。*

<!-- CLAIM_META: CLAIM-12-01 recommendation -->
面向行动的空间表征至少要声明 frame、单位、时间戳、分辨率、已知/未知规则和下游动作；只有外观或点集合不足以定义规划合同。

### 12.1.1 地图是信念，不是世界本身

从传感器生成的 occupancy 是对空间状态的估计。它同时依赖真实场景、传感器模型、标定、位姿估计、时间同步和融合规则。地图中某格被标为 occupied，并不意味着物理世界里存在一个与格边界完全重合的实体；它意味着现有证据在当前表示和阈值下支持占用判断。

这个区别决定了不确定性如何进入行动。深度噪声会沿射线方向扩散表面位置，外参误差会整体移动点云，定位误差会让历史观测与当前地图错位，时间延迟则会把动态目标留在旧位置。只给每格一个置信度，未必能表达这些格子之间的相关误差：一次位姿偏差可能同时移动整面墙。

因此，规划器消费的不应是假定完美的几何真值，而是一份有来源、有时间和有适用范围的空间信念。安全余量、重观测和多传感器核对，是对这些误差结构的响应，不是把概率简单阈值化后的附属步骤。

## 12.2 一条深度射线究竟证明了什么

设传感器沿一条射线在距离 `d` 收到有效回波。在理想不透明表面假设下：传感器到回波之前的射线段可标为观测自由，回波附近可标为占用，回波之后仍是未知。它可能藏着桌腿、行人或另一辆车；“没有看到”不是“确认没有”。

三态 occupancy 因而使用：

- `free`：当前观测对空间为空提供了正证据；
- `occupied`：当前观测对空间被占用提供了正证据；
- `unknown`：证据不足、被遮挡、视野外或时效已过。

概率 occupancy 可保存 `P(occupied)`，但工程接口仍要定义何时映射为自由、占用和未知。阈值附近、不确定度很高或长期未更新的格子，不能静默落到 free。

```mermaid
flowchart TB
    accTitle: FIG-12-02 单条深度射线提供的三态证据
    accDescr: 传感器发出射线，有效回波之前被穿过的空间获得自由证据，回波端点附近获得占用证据，回波之后因遮挡没有观测证据而保持未知。
    S[传感器原点<br/>有效射线开始] --> F[回波前被射线穿过<br/>observed free]
    F --> O[有效回波附近<br/>occupied]
    O -.射线被表面截断.-> U[回波之后或视野之外<br/>unknown]
```

*FIG-12-02：单条射线的三态证据。回波之后没有被射线穿过，仍是未知；unknown 不是低概率 occupied，也不是默认 free。来源：本书原创，CC BY-NC 4.0，2026-09-02。*

### 12.2.1 Unknown 也有不同原因

三态接口把证据不足统一记为 unknown，但推理时仍应保存其原因：

| unknown 来源 | 含义 | 合理的下一步 |
|---|---|---|
| 视野外 | 传感器从未覆盖 | 改变视角或依赖先验地图 |
| 遮挡后 | 射线被前景表面截断 | 等待目标移动或主动绕行观察 |
| 无效测量 | 透明、反光、量程外或传感器故障 | 更换模态、重测或降级 |
| 过期证据 | 过去观测不再代表现在 | 根据动态速度提高更新频率 |
| 冲突证据 | 多源观测或位姿不一致 | 保留冲突并检查标定与同步 |

这些格子都不应直接当作 free，但行动策略可以不同。视野外的静态墙后区域与刚被动态车辆遮挡的路口，不应共享同一个探索优先级。三态是最低安全语义，不是信息表示的终点。

融合多条射线时还要警惕独立性假设。相邻像素、连续帧和同一定位解算产生的误差往往相关；简单重复累积同类观测可能制造过度自信。概率更新规则需要与传感器噪声、时间相关性和动态场景假设共同解释。

## 12.3 点、体素、BEV 与对象：选择损失什么

空间表征没有单一最佳形式，选择取决于动作查询。

| 表征 | 保留的信息 | 适合的查询 | 主要损失或风险 |
| --- | --- | --- | --- |
| 点云 | 观测表面与度量坐标 | 几何、配准、局部表面 | 稀疏，不直接表达 free/unknown |
| 体素/3D occupancy | 三维空间占用 | 碰撞、遮挡、可见性 | 内存随分辨率和范围快速增长 |
| BEV 栅格 | 地面平面上的统一拓扑 | 导航、车道、驾驶规划 | 压缩高度，悬空/叠层可能混淆 |
| 对象列表/轨迹 | 身份、位姿、速度 | 交互、多主体预测 | 漏检对象会从状态中消失 |
| scene graph | 对象及空间/语义关系 | 关系推理、任务规划 | 关系离散化与更新困难 |
| NeRF/3DGS | 连续或显式辐射外观 | novel view、场景重建 | 不自动给出 free、碰撞或动态合同 |
| affordance map | 对特定动作的可行区域/概率 | 接近、抓取、放置、通行 | 强依赖本体、动作与安全约束 |

*TAB-12-01：常见空间表征及其行动接口。它们可以组合，不应按“新旧”排成单一路线。*

体素边长为 `r`，覆盖范围为 `L_x×L_y×L_z` 时，稠密格子数量约为：

\[
N=\left\lceil\frac{L_x}{r}\right\rceil
  \left\lceil\frac{L_y}{r}\right\rceil
  \left\lceil\frac{L_z}{r}\right\rceil.
\]

分辨率减半会令三维稠密格子约增至八倍。稀疏结构、分层地图和 BEV 压缩可以省资源，却不会消除精细碰撞与范围之间的取舍。必须同时报告地图范围、分辨率与机器人/车辆 footprint。

### 12.3.1 米制点怎样落进格子

“点已经在共同 frame”仍不足以得到 cell。二维栅格至少还要声明米制原点 `(x_min,y_min)`、分辨率 `r`、有限范围、轴顺序，以及边界属于哪一格。本章采用 `(x_index,y_index)`，并将第 `(i,j)` 格定义为半开区域：

\[
x\in[x_{min}+ir,\ x_{min}+(i+1)r),\qquad
y\in[y_{min}+jr,\ y_{min}+(j+1)r).
\]

因此米制点到 cell 的映射是

\[
i=\left\lfloor\frac{x-x_{min}}{r}\right\rfloor,\qquad
j=\left\lfloor\frac{y-y_{min}}{r}\right\rfloor.
\]

这里必须用 floor，而不是把浮点数直接转为整数：许多语言的整数转换向 0 截断，`-0.02` 会变成 `0`，从而把原点左侧的越界点错误吸进第 0 格。映射后还要独立检查 `0≤i<W, 0≤j<H`；上边界 `x=x_min+Wr` 属于格外，不是最后一格。数组实现若采用 `[row,column]=[y_index,x_index]`，也必须在接口处显式交换，不能让数学坐标顺序随实现悄悄改变。

半开数学定义还不等于任意浮点实现都能精确命中十进制边界。例如 `0.1` 通常不能被二进制浮点精确表示；项目应固定 dtype、坐标量化与边界容差策略，并用边界两侧的 `nextafter`/整数单位负对照测试。不能随意给所有坐标加 epsilon，因为这会把一侧误差转移到另一侧。本章 fixture 选择二进制可精确表示的 `0.5 m`，没有验证一般浮点栅格化。

这一步是第3章 `frame / unit / timestamp` 合同进入 occupancy 的最后一道离散化接口。Nav2 costmap 的官方配置同样把 `global_frame`、`origin_x/y`、米制 `resolution` 和 footprint 分开登记；这些字段存在仍不证明本书固定栅格与 Nav2 使用相同内部实现。

### 12.3.2 表征选择应从查询倒推

选择空间表征时，应先列出规划器要回答的查询。例如“机械臂沿这条关节轨迹是否碰撞”需要完整连杆 swept volume；“车辆未来三秒能否通过路口”需要地面拓扑、动态参与者与时间；“目标物是否可抓”还需要表面、接近方向和本体约束。一个表征在某项查询上充分，不代表能回答另一项。

坐标 frame 也是表征取舍。ego-centric 地图与当前传感器和局部控制自然对齐，但世界会随本体运动；world/map-centric 地图便于长期融合和全局规划，却高度依赖定位。实践中常同时维护局部 ego map 与全局 map，并明确二者变换的不确定性，而不是假定选定一个 frame 后问题消失。

拓扑与度量几何也不能互相替代。房间连通图可以支持长程任务规划，却无法判断门宽；高分辨率局部体素能检查碰撞，却不适合直接搜索整栋建筑。多层表示的关键是保持对象 ID、frame、时间和不确定性一致，使高层路径能够落回低层可执行区域。

## 12.4 从几何 occupancy 到语义与动态空间

几何 occupancy 只回答“是否占用”。语义 occupancy 再标注道路、车辆、墙面、可移动物等类别；实例与轨迹保留对象身份；动态 occupancy 或 occupancy flow 还估计未来格子状态、速度或流向。

动态状态至少需要：观测时间、预测目标时间、参考 frame、ego-motion 补偿和更新规则。把 `t-1` 的车辆位置与 `t` 的道路放在一起，会得到几何上合法但时间不一致的“幽灵场景”。只预测当前 occupancy 也不能回答一秒后的路径是否会被横穿目标占据。

更新规则本身也必须服从证据语义。若动态目标从格子 A 移到 B，新回波只为 B 的 occupied 提供正证据；它没有自动看穿目标原先遮挡的背景。除非新的射线确实穿过 A，或其他传感器提供清空证据，否则 A 应回到 unknown，而不是直接变成 free。同理，超过新鲜度阈值的旧 free 证据也应回退为 unknown。阈值应来自速度、制动距离、传感器频率和定位误差，而不是只凭地图刷新方便性选取。

对规划 horizon `H`，一种保守碰撞查询是检查 footprint 在每个未来时刻是否与 occupied 或风险未知区域相交。只检查轨迹中心点会漏掉车身、机械臂连杆或安全余量扫过的格子；离散格上的障碍膨胀只是配置空间近似，还需声明 footprint 形状、姿态采样和连续时刻是否覆盖。这里的保守不是永远停止：系统可以主动换视角、减速、请求新观测或选择已知通道，但必须把探索行为和风险预算写进规划器。

### 12.4.1 边缘占用概率不等于一致未来

逐格预测未来 occupied probability，描述的是每个格子的边缘概率。它未必说明这些格子能否在同一个世界中同时占用。例如一辆被遮挡车辆可能向左或向右，两条走廊各有 50% 占用；把两边都画成 0.5 的热图，不能告诉规划器这是一个主体的互斥去向，也不能生成一致轨迹。

对象轨迹、occupancy flow、场景样本和逐格概率因此表达不同结构。对象轨迹保留身份但依赖检测；flow 表达局部运动，却可能在分叉处平均；场景样本保留联合相关性，但有限样本会漏掉低概率事件。规划器若关心碰撞概率，需要说明如何从这些表示聚合到整条 ego trajectory，而不是把逐格概率直接相加。

动态预测还必须与 ego 候选动作建立关系。若其他主体会响应 ego 行为，那么固定的一组 future occupancy 不能同时用于所有候选轨迹；若采用 world-on-rails，则应明确它只近似短时、弱交互反事实。空间表示必须继承第11章的动作与响应协议。

## 12.5 重建得像，不等于可行动

NeRF 和 3D Gaussian Splatting 以新视角渲染和场景重建见长。[Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) 提供 Apache-2.0 的开源 NeRF 工具链 `[O,R1]`；本书没有下载数据或训练该工具链。重建结果可以给 Real2Sim 提供外观和几何先验，但仍需回答：空闲空间如何定义、薄物体是否保留、尺度和坐标是否正确、动态对象如何更新、碰撞几何怎样生成。

2026 年 Google DeepMind 发布的 [D4RT](https://deepmind.google/blog/d4rt-teaching-ai-to-see-the-world-in-four-dimensions/) 将点图、深度、相机与跨时间跟踪统一为动态 4D 重建查询，项目页提供论文与可视结果 `[V/A,R0]`。它是“随时间重建与跟踪”的研究锚点，不自动证明机器人抓取、导航或驾驶安全有效；本书未运行其模型。

<!-- CLAIM_META: CLAIM-12-05 recommendation -->
只有当辐射场、Gaussian、点图或动态重建被控制器或规划器消费时，才应另行验证度量尺度、碰撞几何、未知空间、动态一致性和任务 outcome；渲染指标不能替代这些门禁。若它只用于可视化，应明确标为非行动表示，无需伪装成已通过控制门禁。

## 12.6 affordance：对象、动作与本体的关系

affordance 不是“杯子”类别的同义词。同一把手对两指夹爪、人手和轮式机器人提供不同可能；同一平面可以支撑轻物体，却未必承受机器人本体。可把它理解为：在状态 `s` 下，本体 `b` 执行动作族 `a` 的可行性或成功分布。

因此“可抓取区域”至少依赖末端形状、开口范围、接近方向、碰撞、摩擦和任务；“可行驶区域”依赖车辆 footprint、最小转弯半径、坡度、速度和动态占用。本章 S 档只计算“可达 free 栅格中与 occupied 相邻的接近位置”，这是 affordance 接口 fixture，不是抓取模型。

场景图适合表达 `cup-on-table`、`vehicle-in-lane`、`door-connected-room` 等关系。它能支持任务规划，却可能丢失连续几何。实际系统常用稠密 occupancy 处理碰撞，用对象/图处理语义与长程关系，再通过一致的 ID、frame 和时间连接。

<!-- CLAIM_META: CLAIM-12-06 fact -->
affordance 是状态、动作与本体约束下的关系；物体类别或二维热力图本身不能保证动作可执行。

### 12.6.1 Affordance 还包含可达性与后续状态

一个局部接触在几何上可行，不代表机器人能够从当前配置到达它。affordance 查询至少有三层：目标处是否允许动作，当前本体是否存在无碰路径到达，以及动作完成后的状态是否仍满足任务。例如杯把可夹持，但机械臂可能被桌沿挡住；车辆能进入路口，却可能没有空间驶出。

因此，affordance 具有时间与任务阶段。抓取前关心接近和闭合，抓取后还要承载、搬运和放置；驾驶中“当前可通行”还要检查制动距离、动态占用和下游出口。只输出一张静态可行性热力图，会把动作前提与后果压成同一个不透明分数。

affordance 也不等于策略。它描述哪些动作可能成功或满足约束，策略还需在多个可行选项中根据目标、代价和信息价值作选择。把二者分开，有助于复用同一空间状态支持不同任务。

## 12.7 三态射线、遮挡和坐标偏移（EXP-12-01）

S 档实验在 `7×7` BEV 上从固定原点发出三条无噪声深度射线：射线内部标 free，三个回波端点标 occupied，其余保持 unknown。实验再计算从原点可达的 free 区、障碍旁接近位置、占用格的一格坐标偏移、证据约束的动态更新、方形 footprint 扫掠和观测过期。

<details markdown="1">
<summary>可选：验证本章证据</summary>

```bash
make ch12-test-local
make ch12-smoke-local
make ch12-smoke
```

</details>

| 检查项 | 固定结果 | 解释 |
| --- | ---: | --- |
| free / occupied / unknown | 10 / 3 / 36 | 大部分未被三条射线观测 |
| 可达 free / approach | 8 / 1 | 几何自由不自动等于可接近 |
| 回波后的格子为 unknown | true | 遮挡后方不误标 free |
| occupied 整体横移一格后的 IoU | 0.0 | 小坐标误差可毁掉离散对齐 |
| 三态地图：动态路径更新前安全 | false | 路径含 unknown，保守拒绝 |
| unknown 当 free：同一路径安全 | true | 暴露一次假安全判断 |
| 动态目标移动到路径后安全 | false | 更新后的占用阻断路径 |

*TAB-12-02：`EXP-12-01` 的确定性 CPU smoke。结果由报告脚本生成，不是学习模型 benchmark。*

<!-- CLAIM_META: CLAIM-12-02 result -->
在 `EXP-12-01` 中，回波后方格子保持 unknown；49 个格子中只有 10 个 free、3 个 occupied，另有 36 个 unknown。

<!-- CLAIM_META: CLAIM-12-03 result -->
三个 occupied 格整体横移一格后 occupied IoU 从自对齐的 1 降为 0；这说明该 fixture 对一格坐标偏移敏感，不代表所有真实 occupancy 指标都会降为 0。

<!-- CLAIM_META: CLAIM-12-04 result -->
把 unknown 当 free 会把测试路径判为安全；三态保守查询在更新前因未知拒绝，在动态目标进入路径后因占用拒绝。这个手工例子只验证接口语义，不估计真实误报率。

### 12.7.1 overall accuracy 会奖励错误的多数类

三态地图有36个 unknown、10个 free 和3个 occupied。若在全49格上预测全 unknown，正确36格；若 benchmark 只在13个 observed cell 上计分并预测全 free，正确10格。两个错误 predictor 的 overall accuracy 都超过70%，却漏掉全部 occupied：

| 计分域 / predictor | 分母 | accuracy | occupied recall | occupied IoU | 被 mask 排除 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 全49格 / all-unknown | 49 | 73.47% | 0% | 0% | 0格 |
| 仅 observed / all-free | 13 | 76.92% | 0% | 0% | 36格 unknown |

*TAB-12-03：`EXP-12-01` v5 的类别与 mask 负对照。两个 predictor 均为手写多数类诊断，不是 learned baseline；评测 mask 排除 unknown 只改变计分分母，不改变规划地图中的 unknown 语义。*

<!-- CLAIM_META: CLAIM-12-12 result -->
`EXP-12-01` v5 中，all-unknown 在全域取得36/49即73.47% accuracy，observed-only all-free 取得10/13即76.92%，但两者 occupied recall 与 IoU 都为0。该固定三射线网格只证明 overall accuracy 可能掩盖稀少 occupied，不估计真实数据类别比例、模型性能或碰撞风险。

| 可行动性诊断 | 固定结果 | 分母/解释 |
| --- | ---: | --- |
| 旧目标格，无清空证据 / 有清空证据 | unknown / free | 动态位置变化不等于看见其背景 |
| 3 步中心点路径安全 | true | 只检查 3 个中心格 |
| 半径 1 格 footprint 安全 | false | 扫过 15 个有效格：1 occupied、6 unknown |
| 新鲜 / 过期后的 free 路径安全 | true / false | 1 个过期格回退为 unknown |

*TAB-12-04：`EXP-12-01` 的证据更新、footprint 与新鲜度反例。footprint 是静态方形离散近似，不是连续车辆或机械臂碰撞器。*

<!-- CLAIM_META: CLAIM-12-07 result -->
动态回波离开旧格后，fixture 在没有额外清空证据时把旧格恢复为 unknown；只有显式声明射线已穿过旧格时才标为 free。

<!-- CLAIM_META: CLAIM-12-08 result -->
同一条 3 步路径只检查中心格时安全，但半径 1 格的方形 footprint 扫过 15 个有效格，其中 1 个 occupied、6 个 unknown，保守查询因此拒绝。该结果不代表真实车辆尺寸或连续碰撞率。

<!-- CLAIM_META: CLAIM-12-09 result -->
fixture 中一条 4 格 free 路径原本安全；其中 1 格的观测年龄超过两步阈值后回退为 unknown，路径被保守查询拒绝。两步是教学参数，不是推荐安全阈值。

### 12.7.2 Waypoint 安全不等于路径段安全

路径通常由稀疏 waypoint 表示，但机器人执行的是 waypoint 之间的运动。两个端点都有效，不能推出连接它们的 motion 有效。对整数栅格中的中心路径，本章先用 Bresenham 追踪相邻 waypoint 之间的中心格：

\[
C_{path}=\bigcup_k \operatorname{trace}(q_k,q_{k+1}),
\]

再以每个中心格展开 footprint。OMPL 的官方 state-validity 文档同样区分 state validity 与 motion validity，并说明离散 motion validator 的结果依赖路径段采样分辨率；若有 continuous collision checking，应使用相应 validator，而不是把离散检查当作连续保证。Nav2 的 costmap 文档也把 footprint 明确作为路径碰撞检查的几何输入。

| 查询 | waypoint 数 | 检查的中心格 | 中间 occupied | 判定 |
| --- | ---: | ---: | ---: | --- |
| 只查 waypoint | 2 | 2 | 0 | safe |
| 栅格化连接段 | 2 | 3 | 1 | unsafe |

*TAB-12-05：`EXP-12-01` v5 保留的稀疏 waypoint 反例。第二行只修复整数栅格上的跳格，不是连续时间、连续姿态或车辆动力学碰撞检测。*

<!-- CLAIM_META: CLAIM-12-10 result -->
`EXP-12-01` v5 保留的稀疏路径 `(3,3)→(3,5)` 只检查两个 waypoint 时没有命中 occupied，因允许 unknown 而误判 safe；Bresenham 段栅格化检查三个中心格并检出一个中间 occupied，判为 unsafe。这只验证固定二维整数格的离散路径合同，不证明 continuous collision、转弯扫掠、动态可达性或真实车辆安全。

### 12.7.3 栅格边界也需要负对照

`EXP-12-01` v5 固定 `origin=(0,0) m`、`resolution=0.5 m` 和 `7×7` 半开栅格。格 `(1,0)` 的中心 `(0.75,0.25) m` 可精确往返；另外两例专门检查有限地图边界：

| 米制点 | floor cell / 是否在界内 | 向 0 截断 baseline | 正确解释 |
| --- | --- | --- | --- |
| `(0.75,0.25) m` | `(1,0)` / 是 | `(1,0)` | 格中心的正常对照 |
| `(-0.01,0.25) m` | `(-1,0)` / 否 | `(0,0)` / 是 | 截断产生假纳入 |
| `(3.5,0.25) m` | `(7,0)` / 否 | `(7,0)` / 否 | 半开上边界在格外 |

*TAB-12-06：`EXP-12-01` v5 的米制点—栅格边界负对照。它验证本书固定索引合同，不代表任何外部地图实现。*

<!-- CLAIM_META: CLAIM-12-11 result -->
`EXP-12-01` v5 中，原点左侧 `0.01 m` 的点经 floor 映射到越界 cell `(-1,0)`，而向 0 截断会错误映射到界内 `(0,0)`；`3.5 m` 的上边界映射到 `(7,0)` 并被拒绝。这只验证固定 `0.5 m`、`7×7` 半开栅格的边界合同，不证明 ROS/Nav2、连续碰撞或真实定位行为。

## 12.8 自动驾驶：BEV occupancy、flow 与安全时域

自动驾驶中的 BEV 把相机、lidar、地图和 ego-motion 对齐到车辆或世界平面，适合表达可行驶区域、车道、静态障碍和动态参与者。正文中的最小状态应区分：

- 当前 free/occupied/unknown，而非“无检测框就是自由”；
- 静态语义、实例和可行驶边界；
- 动态对象速度、occupancy flow 或未来占用分布；
- 车辆 footprint、规划轨迹和预测 horizon；
- 相邻轨迹点之间的 motion-validation 分辨率，而不只是 waypoint 数量；
- 定位、标定和时间同步的不确定性。

[Occ3D](https://github.com/Tsinghua-MARS-Lab/Occ3D) 公开了基于 nuScenes/Waymo 的 3D occupancy benchmark 资产 `[O,R1]`，[论文](https://arxiv.org/abs/2304.14365) 讨论从多相机观测预测完整 3D occupancy `[A,R1]`；[OpenScene](https://github.com/OpenDriveLab/OpenScene) 提供基于 nuPlan 的 occupancy-centric 驾驶场景资产 `[O,R1]`。这些仓库证明相应代码/数据说明被公开，不代表本书已获得底层数据许可、下载数据或复现分数。正式使用前必须逐项核验衍生数据条款、非商业限制、体积和版本。

这里要区分“语义标签”和“是否被观测”两个轴。Occ3D 官方生成说明把 lidar 回波所在体素赋予语义、射线穿过的体素标为 free，而其余稀疏或被遮挡体素视为未观测；发布数据另提供 `mask_lidar` / `mask_camera`，官方评测可用 mask 排除未观测体素。**评测时排除未观测体素是一项 benchmark 计分策略，不是允许规划器把它们当 free。** 工程接口可以使用三态枚举，也可以采用 `semantic_label + observation_mask`，但两种编码都不能丢掉 unknown 语义。

驾驶评测不能只报 occupancy IoU。还需按距离、类别、遮挡和时间分桶，并测轨迹碰撞、路线完成、舒适度、干预和校准。一个边界偏移一格的地图可能只轻微影响全局 IoU，却让窄通道规划完全反转；反过来，漂亮 occupancy 也可能未被规划器使用。

学习 occupancy 是感知层，不是安全层。定位漂移、相机掉线、时间延迟或 OOD 天气应触发置信度下降、速度限制、冗余检查或最小风险动作，而不是继续把旧地图当作当前真实状态。

### 12.8.1 当前估计、未来预测、世界模型与场景生成不是同一任务

快速演进的论文常都使用 `occupancy` 或 `4D world`，但输入、输出和用途不同。ICCV 2025 的 UniOcc 明确把 current-frame occupancy prediction 与基于历史的 future occupancy forecasting 分开，并提供 flow 接口；AAAI 2025 的 Drive-OccWorld 再加入动作条件并用未来 occupancy cost 连接规划；ICLR 2025 的 DynamicCity 面向条件化 4D 场景生成。它们适合放在一张接口表中比较，不能仅凭输出都是 voxel 就互换结论。

| 任务 | 最小输入 | 输出回答 | 进入行动前还缺什么 |
| --- | --- | --- | --- |
| 当前 occupancy estimation | 当前传感器、标定、位姿 | “现在何处 free/occupied/unknown？” | 时间新鲜度、定位误差、碰撞查询 |
| future occupancy/flow forecasting | 历史状态或观测 | “未来哪些格会被占用、怎样运动？” | horizon 覆盖、校准、闭环更新 |
| action-conditioned occupancy world model | 历史 + 候选 ego action/trajectory | “采取该动作后可能出现什么？” | 动作覆盖、反事实有效性、独立 outcome scorer |
| 4D scene generation | noise/布局/轨迹/命令等条件 | “能生成哪些时空场景样本？” | 与真实状态的绑定、覆盖度、simulator validity |

*TAB-12-07：occupancy 相关任务的接口区分。来源锚点：UniOcc（ICCV 2025）、Drive-OccWorld（AAAI 2025）、DynamicCity（ICLR 2025）；本书均未运行，表中不引用其性能数字。*

即使 action-conditioned 模型生成了视觉上合理的未来，也不能自动得到正确反事实：训练数据可能没有覆盖该动作，生成器可能只学到场景先验，cost function 还可能遗漏舒适度或交通规则。第11章处理“动作是否真正影响预测”，第17章处理代理 rollout 与 outcome scorer 的误差，第20章处理评测协议；本节只建立空间输出的接口边界。

## 12.9 机器人：接近、抓取与导航

移动机器人先膨胀障碍物或用 footprint 做配置空间碰撞，再在已知自由空间规划；机械臂需要把末端候选姿态、逆运动学、整臂碰撞和接触约束共同检查。二维抓取热力图若没有相机到机器人基座变换，无法变成可执行位姿；点云中的平面若不可达，也不是当前机器人的放置 affordance。

在主动感知中，unknown 可以成为动作目标：移动相机观察物体背面、绕开遮挡或在接触前重新测深度。世界模型则可预测动作如何改变可见性、对象状态和未来 occupancy，但预测地图仍要与真实传感器闭环校正。

主动感知揭示了 unknown 的积极意义：未知不仅是风险，也可能产生信息价值。机器人可以先移动相机再抓取，车辆可以减速以等待遮挡解除。此类动作的即时任务进度可能较低，却能改善后续 belief，因此规划目标需要同时考虑控制后果与观测后果。

但“为了看清而探索”仍受安全约束。不能为了减少地图熵进入无法保证制动或退出的区域。信息增益是可行集内的偏好，不是绕过 occupied/unknown 风险门的理由。

## 12.10 资源、许可与进一步验证

全书资源档位采用[术语表](../glossary.md)中的统一定义。`EXP-12-01` 的 S 档三态栅格只隔离射线证据、坐标边界、路径段、footprint 和观测过期；升级到 RGB-D、多相机或动态 occupancy 时，应按顺序增加传感器噪声、标定与定位误差、时间同步和动态真值，而不是直接用更大的网络掩盖空间合同缺失。

外部数据和模型不是理解三态 occupancy 的前提。确需使用时，应先登记数据体积、输入范围、体素分辨率、预处理缓存和资产许可；Nerfstudio、Occ3D、OpenScene 及其底层数据、权重和衍生资产必须分别核验。完整自动驾驶数据不得由正文命令自动下载。

空间不确定性还应沿查询链传播。定位协方差、深度误差和对象运动不确定性若在栅格化后被丢弃，规划器看到的边界会比证据支持的更精确。障碍膨胀是一种保守近似，但固定膨胀半径无法同时覆盖不同速度、时延和误差方向；安全余量应与当前状态和误差来源绑定。

## 12.11 失效模式与安全边界

重点失效包括：深度尺度错误、外参方向写反、左右手系混用、时间错位、ego-motion 未补偿、unknown 被当 free、稀疏 waypoint 跳过障碍、motion-validation 分辨率过粗、薄物体消失、BEV 高度混叠、动态对象拖影、对象 ID 切换、affordance 不匹配本体，以及模型对视野外过度自信。

调试顺序应从单位/坐标/时间和可视化开始，再检查 occupancy 更新与任务指标，最后讨论网络。连接执行器前，独立碰撞检测、动作限幅、传感器新鲜度、watchdog 和停止策略不可省略。

## 12.12 结果与证据边界

| 类型 | 声明/结果 | 来源 | 状态 | 限制 |
| --- | --- | --- | --- | --- |
| 本书结果 | 三态射线、米制栅格边界、坐标偏移、证据更新、路径段、footprint 与过期 smoke | `EXP-12-01` | CPU smoke | 2D 无噪声手工格子；非外部地图或连续碰撞器 |
| 开源基准 | Occ3D/OpenScene occupancy 资产 | 官方仓库/论文 | `[O/A,R1]` | 本书未下载或运行 |
| 开源工具 | Nerfstudio 场景重建工具链 | 官方仓库 | `[O,R1]` | 本书未训练；非行动证明 |
| 研究案例 | D4RT 动态 4D 重建与跟踪 | 官方页面/论文项目 | `[V/A,R0]` | 本书未独立验证 |
| 未验证 | 24 GB 内轻量 occupancy baseline | 可选 M 档 | planned | 数据、GPU 与资源待测 |

## 小结

可行动空间不是世界本身，也不是某一种网络输出，而是一份带证据来源的信念与查询合同：在什么 frame、时刻和分辨率下，哪里自由、占用或未知，这些判断受哪些传感器、位姿与更新假设支持。

Unknown 至少可能来自视野外、遮挡、无效测量、过期或冲突证据。它们都不能静默变成 free，但可以触发不同的重观测、降速或探索策略。相关的标定与定位误差也不能靠重复融合被错误地“平均掉”。

点云、体素、BEV、对象图和神经重建保留不同信息，应从碰撞、导航、交互或抓取查询反推选择。global topology 与局部 metric geometry、ego frame 与 map frame 常需协同，而不是争夺唯一表示。动态逐格概率还不等于带对象身份和互斥分支的一致未来。

Affordance 是状态、本体、动作和任务阶段之间的关系，还要检查从当前配置能否到达以及动作后是否可继续。只有把这些表征与完整 footprint、连续运动、时间新鲜度、主动感知、下游 outcome 和独立安全层连接，才能从“重建得像”走向“支持行动”。

## 练习

1. **射线更新**：给 `EXP-12-01` 增加最大量程未命中射线，说明哪些格子可标 free。
2. **分辨率实验**：把一格解释为 0.1 m 与 0.5 m，比较同一 footprint 的膨胀结果。
3. **时间实验**：改变 free 证据的新鲜度阈值，按速度和制动距离解释路径判定在哪个时刻改变。
4. **机器人迁移**：为吸盘和两指夹爪分别定义 approach affordance，列出额外状态。
5. **自动驾驶迁移**：设计遮挡车辆切入的 occupancy-flow fixture，分别报告 IoU 和碰撞。
6. **路径离散化**：把两个 waypoint 的间距依次改为 1、2、4 格，比较 waypoint-only、Bresenham 与更细连续碰撞器各自能支持什么结论。
7. **边界规则**：分别用 floor、round 和向 0 截断把 `(-0.01,0.25) m` 映射到 0.5 m 栅格，解释哪个结果符合半开区间；再检查恰好位于上边界的点。
8. **指标审计**：解释 observed mask、unknown 规划语义和 occupied recall 为什么必须分别报告。

## 自检要点

空间题先冻结 frame、米制原点、分辨率、时间和 unknown 规则。以下答案对应本章二维、半开、三态栅格合同，不外推为连续几何或真实传感器证明。

<details markdown="1">
<summary>SELF-CHECK-12-01：最大量程未命中射线</summary>

只有当传感器协议明确“该束有效发射、量程内未收到回波”，且无 dropout、透明/低反射无效码时，才能把从传感器原点之后到最大有效量程之前被射线穿过的格子标为 observed free；没有 occupied endpoint，量程之外仍为 unknown。最大量程落在格子边界时应按半开区间和 ray traversal 规则决定最后一格，不能因 endpoint 数值等于 max range 就标 occupied。还要保存 observation time，旧 free 证据过期后回到 unknown。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-02：分辨率与同一物理 footprint</summary>

必须保持米制 footprint 不变，而不是保持 `footprint_radius_cells` 不变。对半宽 `R` 的方形近似，可先取保守半径 `k=ceil(R/r)`：例如 `R=0.5 m` 时，0.1 m 格取 k=5、检查 11×11 邻域，0.5 m 格取 k=1、检查 3×3；粗格覆盖更量化、薄缝和窄障碍更容易混叠。这个 cell dilation 还不是精确车辆/机器人形状，边界保守度与 cell-center 约定有关；正式比较应在同一米制地图上栅格化 polygon/Minkowski footprint，并报告 false-safe/false-blocked。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-03：新鲜度、速度与制动距离</summary>

当前 fixture 的 cell 在 step 0 观测、step 3 查询，规则是 `age>max_age` 才过期：阈值 0、1、2 时路径因该 cell 变 unknown 而不安全，阈值≥3 时仍保留 free。工程阈值应换算为秒，并约束未观测期间可能位移 `v_rel τ`，同时考虑感知/规划/制动延迟和停止距离 `v²/(2a)`；速度越高、相对目标越快或定位误差越大，可接受 τ 通常越小。路径从 safe 变 unknown 的时刻只是触发重新观测、减速或 fallback，不证明此处已有障碍。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-04：吸盘与两指夹爪 affordance</summary>

吸盘 approach 至少要求目标表面片平整、法向与接近轴对齐、有效密封面积、材质/孔隙可吸附、末端和手臂路径无碰撞，并保留真空状态与负载上限。两指夹爪还需可达的对向接触面、开口/指厚、抓取宽度、摩擦锥、夹持力、质心/扭矩、手指闭合扫掠和防碰撞姿态。二者都依赖机器人 base/EEF frame、IK、关节限位、对象 pose uncertainty 和任务后的搬运方向；“与 occupied 相邻的 free cell”只够做接近位置 fixture。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-05：遮挡切入的 occupancy-flow</summary>

构造同一 ego 轨迹下的三时刻真值：车辆先在遮挡后为 unknown，随后进入相邻车道，并在预测 horizon 与 ego swept footprint 相交；模型输出每个未来时刻的 occupied probability/flow。逐 horizon 报 observed-mask 与全规划域 IoU、flow endpoint error、risk coverage，再用同一 footprint 做碰撞/最小 TTC。IoU 与碰撞必须分开：大量道路格预测正确可使 IoU 很高，但漏掉唯一冲突格仍产生碰撞；反之整体 IoU 低也不必然碰撞。不得用评测 mask 排除 unknown 后，再让 planner 把这些格当 free。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-06：waypoint 间距与碰撞结论</summary>

间距 1 格时相邻整数 waypoint 已覆盖中心格，但 footprint、对角角落和两时刻之间的连续扫掠仍可能遗漏；间距 2 或 4 格时 waypoint-only 会产生 1 或 3 格级空洞，可能直接跳过障碍。Bresenham 能检查连接线经过的离散中心格，当前 fixture 因而发现 `(3,4)`，但它不是 supercover，也不覆盖 sub-cell 障碍、姿态变化或曲线偏离。更细连续碰撞器只有在几何、插值、采样上界和 swept volume 都冻结后，才能支持相应连续路径结论。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-07：半开边界映射</summary>

相对坐标除以 0.5 得 `(-0.02,0.5)`。Floor 映射为 `(-1,0)`，正确表示 x 在原点左侧、整体越界；向 0 截断得到 `(0,0)`，错误吸入地图。Python 的 ties-to-even `round` 得 `(0,0)`；其他 round 规则可能把 y 映为 1，但无论哪种都不符合按下边界分格的半开合同。对有限 7×7、原点 0、分辨率 0.5 m 的栅格，x 上边界 3.5 m 映为 index 7，必须判 out of bounds；任一内部边界也属于右/上侧下一格，而不是前一格。

</details>

<details markdown="1">
<summary>SELF-CHECK-12-08：计分 mask 与规划 unknown</summary>

Observed mask 回答“哪些 cell 进入当前 benchmark 分母”，unknown 则回答“规划器对哪些空间缺少自由/占用证据”，二者属于不同接口。当前 fixture 的 observed-only 分母为13，排除36个 unknown；all-free 在其中命中10个 free，accuracy 为10/13，但三个 occupied 全漏，recall/IoU 都为0。最低报告应同时列全域与 masked 分母、free/occupied/unknown support、逐类 precision/recall/IoU、距离/遮挡分桶，以及规划 swept-footprint 冲突。被评测 mask 排除的 cell 在规划地图中仍应保留 unknown，除非另有清空证据；不能把“不计分”改写成“可通行”。

</details>

## 延伸阅读

- Tian et al., [Occ3D](https://arxiv.org/abs/2304.14365) 与[官方仓库](https://github.com/Tsinghua-MARS-Lab/Occ3D)，`[A/O,R1]`；
- Wang et al., [OpenOccupancy](https://arxiv.org/abs/2303.03991)，`[A,R1]`，多模态 occupancy benchmark；
- OpenDriveLab, [OpenScene](https://github.com/OpenDriveLab/OpenScene)，`[O,R1]`；
- Wang et al., [UniOcc（ICCV 2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_UniOcc_A_Unified_Benchmark_for_Occupancy_Forecasting_and_Prediction_in_ICCV_2025_paper.html)，`[P,R0]`，区分 current prediction、future forecasting 与 flow；
- Yang et al., [Drive-OccWorld（AAAI 2025）](https://ojs.aaai.org/index.php/AAAI/article/view/33010)，`[P,R0]`，动作条件 4D occupancy 与 planning 接口；
- Bian et al., [DynamicCity（ICLR 2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/6506964d22ede4d36adae956e6a9919a-Abstract-Conference.html)，`[P,R0]`，条件化 4D occupancy generation；
- Nerfstudio, [开源 NeRF 工具链](https://github.com/nerfstudio-project/nerfstudio)，`[O,R1]`；
- Google DeepMind, [D4RT 官方介绍](https://deepmind.google/blog/d4rt-teaching-ai-to-see-the-world-in-four-dimensions/) 与[论文项目页](https://d4rt-paper.github.io/)，`[V/A,R0]`。
- OMPL, [State Validity Checking](https://docs.ros.org/en/iron/p/ompl/doc/markdown/stateValidation.html)，离散 motion validation 的分辨率与连续检查边界；
- Nav2, [Costmap 2D](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/)，footprint 与 costmap collision checking 接口。

## 下一章接口

第15章会把视觉/语言/空间状态接入动作策略；第19章会把 occupancy、重建资产和动力学放进 Real2Sim/Sim2Real；第22章可选择“3D/occupancy 表征用于抓取或导航”作为综合项目。
