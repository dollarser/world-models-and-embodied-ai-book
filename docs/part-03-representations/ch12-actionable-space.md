# 第12章 可行动的空间表征

> 状态：`reviewed`
> 资料核查日期：2026-09-02
> 关联实验：`EXP-12-01`
> 关联声明：`CLAIM-12-01`～`CLAIM-12-11`
> 关联图表：`FIG-12-01` / `FIG-12-02` / `TAB-12-01`～`TAB-12-06`
> 资源档位：S / M / L1 / L2
> GPU 状态：待验证

## 本章契约

### 核心问题

怎样把相机看到的像素变成能回答“哪里可走、哪里会碰、从哪里接近、物体正在往哪动”的空间状态？一幅看起来真实的三维重建，为什么不一定能直接用于机器人或自动驾驶？

### 先修知识

- 已具备：第3章的坐标系、针孔投影、深度、点云与 BEV 最小桥接；第9章的任务指标与失败分析；
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

读者应能从带 frame/单位/时间戳的 RGB-D 或点云构造简化 occupancy，解释 free/occupied/unknown，分析分辨率、遮挡、坐标偏移和动态更新，拒绝只检查稀疏 waypoint 的路径假安全，并把空间状态连接到导航、接近、抓取或驾驶规划。

## 12.1 从像素到行动约束

RGB 告诉我们表面看起来怎样，深度把像素连接到尺度，标定把不同传感器和时刻放入共同坐标系。第3章已经给出反投影：像素 `(u,v)` 和深度 `d` 经过内参可得到相机坐标点，再由外参变换到机器人、车辆或世界 frame。本章关心接下来的压缩：哪些空间证据必须保留，才能支持动作？

```mermaid
flowchart LR
    accTitle: FIG-12-01 从传感器证据到可行动空间
    accDescr: RGB-D、激光雷达和多视图证据变换为带坐标系与时间的点，再压缩成体素或俯视表示、三态占用、语义速度和可行动区域供规划使用。
    S[RGB-D / lidar / 多视图] --> P[带 frame 与时间戳的点]
    P --> V[体素 / BEV / 对象与关系]
    V --> O[free / occupied / unknown]
    O --> D[语义、速度、置信度]
    D --> A[可行驶/可接近/可抓取区域]
    A --> C[规划、控制与独立安全检查]
```

*FIG-12-01：从传感器证据到可行动空间的最小链路。每次压缩都应保留 frame、时间与未知状态。来源：本书原创，MIT，2026-08-31。*

`CLAIM-12-01`（recommendation）：面向行动的空间表征至少要声明 frame、单位、时间戳、分辨率、已知/未知规则和下游动作；只有外观或点集合不足以定义规划合同。

## 12.2 一条深度射线究竟证明了什么

设传感器沿一条射线在距离 `d` 收到有效回波。在理想不透明表面假设下：传感器到回波之前的射线段可标为观测自由，回波附近可标为占用，回波之后仍是未知。它可能藏着桌腿、行人或另一辆车；“没有看到”不是“确认没有”。

三态 occupancy 因而使用：

- `free`：当前观测对空间为空提供了正证据；
- `occupied`：当前观测对空间被占用提供了正证据；
- `unknown`：证据不足、被遮挡、视野外或时效已过。

概率 occupancy 可保存 `P(occupied)`，但工程接口仍要定义何时映射为自由、占用和未知。阈值附近、不确定度很高或长期未更新的格子，不能静默落到 free。

```text
传感器  · · · · X ? ?
证据    free    occupied  unknown
```

*FIG-12-02：单条射线的三态证据。`X` 后方没有被回波穿过，仍是未知。来源：本书原创，MIT，2026-08-31。*

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

## 12.4 从几何 occupancy 到语义与动态空间

几何 occupancy 只回答“是否占用”。语义 occupancy 再标注道路、车辆、墙面、可移动物等类别；实例与轨迹保留对象身份；动态 occupancy 或 occupancy flow 还估计未来格子状态、速度或流向。

动态状态至少需要：观测时间、预测目标时间、参考 frame、ego-motion 补偿和更新规则。把 `t-1` 的车辆位置与 `t` 的道路放在一起，会得到几何上合法但时间不一致的“幽灵场景”。只预测当前 occupancy 也不能回答一秒后的路径是否会被横穿目标占据。

更新规则本身也必须服从证据语义。若动态目标从格子 A 移到 B，新回波只为 B 的 occupied 提供正证据；它没有自动看穿目标原先遮挡的背景。除非新的射线确实穿过 A，或其他传感器提供清空证据，否则 A 应回到 unknown，而不是直接变成 free。同理，超过新鲜度阈值的旧 free 证据也应回退为 unknown。阈值应来自速度、制动距离、传感器频率和定位误差，而不是只凭地图刷新方便性选取。

对规划 horizon `H`，一种保守碰撞查询是检查 footprint 在每个未来时刻是否与 occupied 或风险未知区域相交。只检查轨迹中心点会漏掉车身、机械臂连杆或安全余量扫过的格子；离散格上的障碍膨胀只是配置空间近似，还需声明 footprint 形状、姿态采样和连续时刻是否覆盖。这里的保守不是永远停止：系统可以主动换视角、减速、请求新观测或选择已知通道，但必须把探索行为和风险预算写进规划器。

## 12.5 重建得像，不等于可行动

NeRF 和 3D Gaussian Splatting 以新视角渲染和场景重建见长。[Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) 提供 Apache-2.0 的开源 NeRF 工具链 `[O,R1]`；本书没有在当前无 GPU 环境下载数据或训练。重建结果可以给 Real2Sim 提供外观和几何先验，但仍需回答：空闲空间如何定义、薄物体是否保留、尺度和坐标是否正确、动态对象如何更新、碰撞几何怎样生成。

2026 年 Google DeepMind 发布的 [D4RT](https://deepmind.google/blog/d4rt-teaching-ai-to-see-the-world-in-four-dimensions/) 将点图、深度、相机与跨时间跟踪统一为动态 4D 重建查询，项目页提供论文与可视结果 `[V/A,R0]`。它是“随时间重建与跟踪”的研究锚点，不自动证明机器人抓取、导航或驾驶安全有效；本书未运行其模型。

`CLAIM-12-05`（recommendation）：只有当辐射场、Gaussian、点图或动态重建被控制器或规划器消费时，才应另行验证度量尺度、碰撞几何、未知空间、动态一致性和任务 outcome；渲染指标不能替代这些门禁。若它只用于可视化，应明确标为非行动表示，无需伪装成已通过控制门禁。

## 12.6 affordance：对象、动作与本体的关系

affordance 不是“杯子”类别的同义词。同一把手对两指夹爪、人手和轮式机器人提供不同可能；同一平面可以支撑轻物体，却未必承受机器人本体。可把它理解为：在状态 `s` 下，本体 `b` 执行动作族 `a` 的可行性或成功分布。

因此“可抓取区域”至少依赖末端形状、开口范围、接近方向、碰撞、摩擦和任务；“可行驶区域”依赖车辆 footprint、最小转弯半径、坡度、速度和动态占用。本章 S 档只计算“可达 free 栅格中与 occupied 相邻的接近位置”，这是 affordance 接口 fixture，不是抓取模型。

场景图适合表达 `cup-on-table`、`vehicle-in-lane`、`door-connected-room` 等关系。它能支持任务规划，却可能丢失连续几何。实际系统常用稠密 occupancy 处理碰撞，用对象/图处理语义与长程关系，再通过一致的 ID、frame 和时间连接。

`CLAIM-12-06`（fact）：affordance 是状态、动作与本体约束下的关系；物体类别或二维热力图本身不能保证动作可执行。

## 12.7 EXP-12-01：三态射线、遮挡和坐标偏移

S 档实验在 `7×7` BEV 上从固定原点发出三条无噪声深度射线：射线内部标 free，三个回波端点标 occupied，其余保持 unknown。实验再计算从原点可达的 free 区、障碍旁接近位置、占用格的一格坐标偏移、证据约束的动态更新、方形 footprint 扫掠和观测过期。

```bash
make ch12-test-local
make ch12-smoke-local
make ch12-smoke
```

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

`CLAIM-12-02`（result）：在 `EXP-12-01` 中，回波后方格子保持 unknown；49 个格子中只有 10 个 free、3 个 occupied，另有 36 个 unknown。

`CLAIM-12-03`（result）：三个 occupied 格整体横移一格后 occupied IoU 从自对齐的 1 降为 0；这说明该 fixture 对一格坐标偏移敏感，不代表所有真实 occupancy 指标都会降为 0。

`CLAIM-12-04`（result）：把 unknown 当 free 会把测试路径判为安全；三态保守查询在更新前因未知拒绝，在动态目标进入路径后因占用拒绝。这个手工例子只验证接口语义，不估计真实误报率。

| 可行动性诊断 | 固定结果 | 分母/解释 |
| --- | ---: | --- |
| 旧目标格，无清空证据 / 有清空证据 | unknown / free | 动态位置变化不等于看见其背景 |
| 3 步中心点路径安全 | true | 只检查 3 个中心格 |
| 半径 1 格 footprint 安全 | false | 扫过 15 个有效格：1 occupied、6 unknown |
| 新鲜 / 过期后的 free 路径安全 | true / false | 1 个过期格回退为 unknown |

*TAB-12-03：`EXP-12-01` 的证据更新、footprint 与新鲜度反例。footprint 是静态方形离散近似，不是连续车辆或机械臂碰撞器。*

`CLAIM-12-07`（result）：动态回波离开旧格后，fixture 在没有额外清空证据时把旧格恢复为 unknown；只有显式声明射线已穿过旧格时才标为 free。

`CLAIM-12-08`（result）：同一条 3 步路径只检查中心格时安全，但半径 1 格的方形 footprint 扫过 15 个有效格，其中 1 个 occupied、6 个 unknown，保守查询因此拒绝。该结果不代表真实车辆尺寸或连续碰撞率。

`CLAIM-12-09`（result）：fixture 中一条 4 格 free 路径原本安全；其中 1 格的观测年龄超过两步阈值后回退为 unknown，路径被保守查询拒绝。两步是教学参数，不是推荐安全阈值。

### 12.7.1 Waypoint 安全不等于路径段安全

路径通常由稀疏 waypoint 表示，但机器人执行的是 waypoint 之间的运动。两个端点都有效，不能推出连接它们的 motion 有效。对整数栅格中的中心路径，本章先用 Bresenham 追踪相邻 waypoint 之间的中心格：

\[
C_{path}=\bigcup_k \operatorname{trace}(q_k,q_{k+1}),
\]

再以每个中心格展开 footprint。OMPL 的官方 state-validity 文档同样区分 state validity 与 motion validity，并说明离散 motion validator 的结果依赖路径段采样分辨率；若有 continuous collision checking，应使用相应 validator，而不是把离散检查当作连续保证。Nav2 的 costmap 文档也把 footprint 明确作为路径碰撞检查的几何输入。

| 查询 | waypoint 数 | 检查的中心格 | 中间 occupied | 判定 |
| --- | ---: | ---: | ---: | --- |
| 只查 waypoint | 2 | 2 | 0 | safe |
| 栅格化连接段 | 2 | 3 | 1 | unsafe |

*TAB-12-04：`EXP-12-01` v4 保留的稀疏 waypoint 反例。第二行只修复整数栅格上的跳格，不是连续时间、连续姿态或车辆动力学碰撞检测。*

`CLAIM-12-10`（result）：`EXP-12-01` v4 保留的稀疏路径 `(3,3)→(3,5)` 只检查两个 waypoint 时没有命中 occupied，因允许 unknown 而误判 safe；Bresenham 段栅格化检查三个中心格并检出一个中间 occupied，判为 unsafe。这只验证固定二维整数格的离散路径合同，不证明 continuous collision、转弯扫掠、动态可达性或真实车辆安全。

### 12.7.2 栅格边界也需要负对照

`EXP-12-01` v4 固定 `origin=(0,0) m`、`resolution=0.5 m` 和 `7×7` 半开栅格。格 `(1,0)` 的中心 `(0.75,0.25) m` 可精确往返；另外两例专门检查有限地图边界：

| 米制点 | floor cell / 是否在界内 | 向 0 截断 baseline | 正确解释 |
| --- | --- | --- | --- |
| `(0.75,0.25) m` | `(1,0)` / 是 | `(1,0)` | 格中心的正常对照 |
| `(-0.01,0.25) m` | `(-1,0)` / 否 | `(0,0)` / 是 | 截断产生假纳入 |
| `(3.5,0.25) m` | `(7,0)` / 否 | `(7,0)` / 否 | 半开上边界在格外 |

*TAB-12-05：`EXP-12-01` v4 的米制点—栅格边界负对照。它验证本书固定索引合同，不代表任何外部地图实现。*

`CLAIM-12-11`（result）：`EXP-12-01` v4 中，原点左侧 `0.01 m` 的点经 floor 映射到越界 cell `(-1,0)`，而向 0 截断会错误映射到界内 `(0,0)`；`3.5 m` 的上边界映射到 `(7,0)` 并被拒绝。这只验证固定 `0.5 m`、`7×7` 半开栅格的边界合同，不证明 ROS/Nav2、连续碰撞或真实定位行为。

## 12.8 自动驾驶正文：BEV occupancy、flow 与安全时域

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

*TAB-12-06：occupancy 相关任务的接口区分。来源锚点：UniOcc（ICCV 2025）、Drive-OccWorld（AAAI 2025）、DynamicCity（ICLR 2025）；本书均未运行，表中不引用其性能数字。*

即使 action-conditioned 模型生成了视觉上合理的未来，也不能自动得到正确反事实：训练数据可能没有覆盖该动作，生成器可能只学到场景先验，cost function 还可能遗漏舒适度或交通规则。第11章处理“动作是否真正影响预测”，第17章处理代理 rollout 与 outcome scorer 的误差，第20章处理评测协议；本节只建立空间输出的接口边界。

## 12.9 机器人正文：接近、抓取与导航

移动机器人先膨胀障碍物或用 footprint 做配置空间碰撞，再在已知自由空间规划；机械臂需要把末端候选姿态、逆运动学、整臂碰撞和接触约束共同检查。二维抓取热力图若没有相机到机器人基座变换，无法变成可执行位姿；点云中的平面若不可达，也不是当前机器人的放置 affordance。

在主动感知中，unknown 可以成为动作目标：移动相机观察物体背面、绕开遮挡或在接触前重新测深度。世界模型则可预测动作如何改变可见性、对象状态和未来 occupancy，但预测地图仍要与真实传感器闭环校正。

## 12.10 资源、许可与升级路径

S 档 `EXP-12-01` 使用 Python 标准库、CPU、零下载和 MIT 程序化 fixture；它只验证三态地图、连通、半开米制栅格边界、坐标误差、证据更新、Bresenham 路径段、离散 footprint 与观测过期。

M 档可在用户明确同意数据条款与下载量后，使用许可允许的小型 RGB-D/仿真子集训练轻量 depth/occupancy baseline，默认不超过 24 GB 单卡。应先记录数据体积、预处理缓存、输入范围、体素分辨率和峰值显存。当前无 GPU 阶段不执行。

L1 可加入多相机或短时动态 occupancy；L2 最多 2×80 GB，只作为明确选做的研究扩展，不是阅读前置。完整自动驾驶数据常达到数十 GB 以上且有独立许可，不应由命令自动下载。Nerfstudio、Occ3D、OpenScene 及底层数据的代码、权重、数据和衍生资产许可必须分别记录。

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
| 未验证 | 24 GB 内轻量 occupancy baseline | 后续 M 档 | planned | 数据、GPU 与资源待测 |

## 小结

可行动空间不是某一种网络输出，而是一份查询合同：在什么 frame、时刻和分辨率下，哪里自由、占用或未知，什么对象在运动，哪个本体能执行什么动作。点云、BEV、occupancy、对象图和神经重建可以互补；只有与碰撞、抓取、导航、驾驶 outcome 和安全层连接，才能从“重建得像”走向“支持行动”。

## 练习

1. **射线更新**：给 `EXP-12-01` 增加最大量程未命中射线，说明哪些格子可标 free。
2. **分辨率实验**：把一格解释为 0.1 m 与 0.5 m，比较同一 footprint 的膨胀结果。
3. **时间实验**：改变 free 证据的新鲜度阈值，按速度和制动距离解释路径判定在哪个时刻改变。
4. **机器人迁移**：为吸盘和两指夹爪分别定义 approach affordance，列出额外状态。
5. **自动驾驶迁移**：设计遮挡车辆切入的 occupancy-flow fixture，分别报告 IoU 和碰撞。
6. **路径离散化**：把两个 waypoint 的间距依次改为 1、2、4 格，比较 waypoint-only、Bresenham 与更细连续碰撞器各自能支持什么结论。
7. **边界规则**：分别用 floor、round 和向 0 截断把 `(-0.01,0.25) m` 映射到 0.5 m 栅格，解释哪个结果符合半开区间；再检查恰好位于上边界的点。

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

## 验收与审查记录

```text
本地检查：make check-local
严格检查：make check
章节 smoke：make ch12-smoke
文档构建：make docs-build
```

- 内容审查：通过；
- 代码审查：通过；
- 一致性审查：通过；
- 教学审查：通过；
- 审查记录路径：`reviews/ch12-metric-grid-and-task-boundary-review-2026-09-02.md`；
- 已知限制：固定 0.5 m fixture 未验证任意十进制分辨率的浮点边界；未训练 3D/occupancy 模型，Bresenham 不是 supercover 或 continuous collision checking，未下载真实数据，未运行仿真或 GPU；
- 下一步：在真实 RGB-D/驾驶数据上加入标定噪声、连续 swept volume、姿态插值与动态 occupancy；当前接口已与第3、4、9、10、11、15、19章核对。
