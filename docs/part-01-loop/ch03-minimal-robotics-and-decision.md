# 第3章 具身任务的最小机器人学与决策基础

## 本章契约

### 核心问题

一个没有 3D 视觉和机器人学经验的 CV 工程师，至少要掌握哪些坐标、几何、多模态观测、动作和决策接口，才能正确读取后续世界模型、VLA、BEV 与仿真研究？

### 先修知识

- 已具备：向量、矩阵乘法、像素坐标和 Python 基础；
- 本章补齐：相机投影、坐标变换、多模态观测有效性、点云/BEV 直觉、运动学、控制频率和 MDP/POMDP；
- 不要求：多视图几何证明、李代数推导、机器人动力学、真实标定板或硬件。

### 非目标

- 不替代完整机器人学、控制或 3D 视觉课程；
- 不把理想针孔反投影当作真实相机标定；
- 不把安装 ROS、MuJoCo 或 GPU 环境设为理解本章的前提；
- 不把二维运动学 smoke 当作实机控制与安全验收。

### 学完后的可验证产出

读者应能：

1. 区分像素、相机、机器人/车体和世界坐标系；
2. 用内参反投影 RGB-D 像素，并显式变换到目标坐标系；
3. 将少量点栅格化为简化 occupancy/BEV；
4. 区分关节、末端、车辆和高层动作；
5. 说明 MDP 与 POMDP 中状态、观测、信念、规划和策略的关系；
6. 定位轴向、单位、外参、多模态有效性、时间同步和控制频率错误；
7. 由位姿时间偏移和已知运动，量化一个点的空间错位，而不把“最新位姿”误当成“采样时位姿”。

## 3.1 先建立闭环，而不是先背术语

具身系统从传感器获得观测，根据内部状态估计选择动作，环境被动作改变后再产生新观测。几何回答“量在哪里、相对于谁”，运动学回答“动作会把本体带到哪里”，决策模型回答“在不确定性下该选哪个动作”。

```mermaid
flowchart TB
    accTitle: FIG-03-01 图 3-1 具身智能的观测决策闭环
    accDescr: 不可直接获得的真实状态产生观测，智能体由观测形成状态或信念并选择动作，环境转移后再返回新观测。
    E["真实状态 $$e_t$$"] --> S[传感器]
    S --> O["观测 $$o_t$$"]
    O --> B["状态/信念 $$z_t$$"]
    B --> P[策略或规划器]
    P --> A["动作 $$a_t$$"]
    A --> C[下层控制器与安全层]
    C --> E2["下一真实状态 $$e_{t+1}$$"]
    E2 --> S
```

*图 3-1：本章统一的具身闭环接口。真实状态通常不可直接获得；学习模型使用观测构造任务相关的状态或信念。来源：本书原创，CC BY-NC 4.0，2026-08-31。*<!-- INTERNAL_ASSET_ID: FIG-03-01 -->

在图像分类中，像素坐标和标签通常足够；在机器人或车辆中，“目标在 `(1, 0, 0)`”如果没有坐标系、单位和时间戳就没有可执行含义。后续所有数组都应当被看成“数值 + frame + unit + timestamp + convention”。

<!-- CLAIM_META: CLAIM-03-01 recommendation -->
任何几何、状态或动作张量的接口，都应显式记录坐标系、单位、时间戳和轴向约定；shape 相同不代表语义兼容。

### 3.1.1 初学者先分清六种量

“图里一个点”“空间里一个点”和“地图中的一个格”不是同一种对象。第一次阅读只需沿下面六级检查，不必先掌握多视图几何：

| 量 | 最小写法 | 依赖什么 | 还不能回答什么 |
| --- | --- | --- | --- |
| 像素 | `(u,v)`，单位 px | 图像尺寸与像素原点 | 离相机多远 |
| 深度/range | `d` 或 `r`，单位 m | 传感器定义、有效 mask | 单独一个数不能给出横向位置 |
| 相机点 | $p_{\text{camera}}=(X,Y,Z)$ | 像素、深度类型、内参 | 不知道机器人/车辆中的方向 |
| 本体点 | $p_{\text{body}}$ | 相机点与 $T_{\text{body_camera}}$ | 不知道全局地图位置 |
| 位姿/变换 | $T_{\text{target_source}}(t)$ | 源/目标 frame、时刻与约定 | 不等同某个物体点本身 |
| voxel/BEV cell | `(i,j,k)` 或 `(i,j)` | 范围、分辨率、原点与栅格规则 | 没有点不等于确认 free |

*表 3-1：零基础 3D 量的最小区分。每向下一级都增加假设；逆向压缩通常会丢信息。*<!-- INTERNAL_ASSET_ID: TAB-03-01 -->

这里的 coordinate frame 是“用哪组原点和轴表达数值”，不要与视频中的一帧 image frame 混淆。本书保留英文 `frame` 时，会通过 `frame_id`、`video frame` 或上下文明确是哪一种。

### 3.1.2 多模态观测不是把数组拼在一起

具身系统的 observation 往往同时包含 RGB、深度、关节编码器、末端位姿、夹爪状态、触觉、力/力矩、底盘或车辆状态。它们观测的是同一世界，却不一定在同一时刻采样，也不具有相同的 frame、频率、延迟、噪声和失效方式。把最新到达的各个数组直接拼接，会制造一个现实中从未同时存在过的“伪快照”。

每种模态至少需要保留自己的 `timestamp`、`frame_id`、单位、有效位和来源序号。融合时还要声明目标时刻：是把所有信号对齐到相机曝光时刻、控制决策时刻，还是维护一个随异步观测更新的 belief。插值只适用于有明确连续语义的量；关节角可以在满足运动假设时插值，接触开关、任务阶段和急停状态却不能用数值平均伪造中间状态。缺失也不是零值：无触觉包不表示“没有接触”，深度无效不表示“空间空闲”。

多模态融合可以发生在输入、特征或状态估计层，但层级名称本身不保证信息被正确使用。早期拼接便于联合建模，也更容易受时间错位和量纲差异影响；后期融合便于保留各模态质量与缺失状态，却可能丢掉细粒度对应关系；filtering 则把不同模态视为对 latent state 的异步证据，需要显式的预测与更新模型。选择哪一种，应由任务中哪些隐藏状态需要消歧决定，而不是由传感器数量决定。

杯子被机械臂遮挡时，视觉可能暂时失去接触点；关节位置只能说明夹爪到了哪里，不能证明杯子已经夹稳；触觉或电流变化能增加接触证据，也可能来自桌面碰撞或机构摩擦。可靠 belief 应保留这些来源及其不确定性，并在新证据冲突时允许回退到“是否抓住尚不确定”。这条原则会在第6章进入 posterior 更新，在第15章进入 VLA 输入合同，在第21章进入新鲜度与故障降级。

## 3.2 从像素到相机坐标：只需一个可检查的针孔模型

像素 `(u,v)` 表示图像平面的位置，深度 `d` 提供沿相机光轴的尺度。为便于桥接，本章 fixture 采用常见光学坐标约定：`x` 向右、`y` 向下、`z` 向前，深度单位为米。不同库和硬件可能不同，必须读取其文档而不是猜测。

忽略畸变时，内参 $f_x,f_y,c_x,c_y$ 将像素反投影为相机坐标：

\[
X_c=(u-c_x)d/f_x,\qquad Y_c=(v-c_y)d/f_y,\qquad Z_c=d.
\]

这里 $f_x,f_y$ 用像素表示焦距，$(c_x,c_y)$ 是主点。它不是“从单张 RGB 猜深度”：深度必须来自 RGB-D、双目、LiDAR、模型预测或其他来源，来源和不确定性要单独记录。

还要先问设备给的是 **z-depth** 还是沿成像射线的欧氏 **range**。上式要求 \(Z_c=d\)；若给定 range \(r\)，应先令

\[
Z_c=\frac{r}{\sqrt{((u-c_x)/f_x)^2+((v-c_y)/f_y)^2+1}}.
\]

两者在主点处相等，离主点越远差异越大。fixture 的离轴归一化坐标为 `(1,0)`：数值为 1 m 的 z-depth 对应射线距离 \(\sqrt{2}\) m，而 1 m range 对应 \(Z_c=1/\sqrt{2}\) m。

最小自检是 round trip：把反投影点再投影回像素，误差应接近数值精度。但相同的错误内参用于正反两程也可能自洽，所以 round trip 只验证实现闭合，不验证标定正确。如果 round trip 通过但点云尺度错 1000 倍，通常是毫米/米错误；如果中心附近正确、边缘系统性弯曲，可能是畸变未处理；如果 RGB 与深度边缘错位，要检查配准与时间同步。

OpenCV 官方标定接口区分针孔与 fisheye 等相机模型。实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> 只覆盖无畸变针孔模型，不能证明真实设备已标定。

## 3.3 外参：同一个点，换一个观察者

点从源坐标系 `s` 变换到目标坐标系 `t`：

\[
{}^{t}p = {}^{t}R_s\,{}^{s}p + {}^{t}t_s.
\]

记号左上角表示“这个量用哪个 frame 表达”。`R` 是旋转，`t` 是源坐标原点在目标坐标中的位置。齐次变换把两者放入 `4×4` 矩阵，属于特殊欧氏群 $SE(3)$；本书只要求会组合和检查变换，不要求推导李群指数映射。

刚体旋转不只是任意 `3×3` 数组。proper rotation 必须满足 $R^\top R=I$ 且 $\det(R)=+1$：缩放/剪切不满足正交性，镜像虽然可能正交却有 $\det(R)=-1$。若代码直接用 $R^\top$ 当逆矩阵而不检查这些条件，错误矩阵也可能产生看似完整的点云。

变换方向是最常见错误。$T_{\text{body_camera}}$ 应解释为“把 camera 表达的点变到 body”，不能仅靠变量名中的两个 frame 猜乘法方向。链式变换要让相邻 frame 抵消，例如：

```text
p_world = T_world_body @ T_body_camera @ p_camera
```

因此 $T_{world\leftarrow camera}=T_{world\leftarrow body}T_{body\leftarrow camera}$。组合后的平移不是把两个三维向量直接相加，而是先把中间变换的平移旋转到 target frame，再相加。相机安装外参通常相对 body 固定，$T_{\text{world_body}}(t)$ 却随机器人运动而变化；二者还必须对应同一时间基准。

推荐的三项自检：原点变到哪里、单位轴变到哪里、正变换后再乘逆变换能否回到原点。只检查最终可视化“看起来差不多”不足以发现左右手系或轴交换。

本章 body frame 明确采用 `x` 向前、`y` 向左、`z` 向上。因此 camera optical 到 body 不可能直接使用单位旋转；固定轴映射为：

\[
{}^bR_c=\begin{bmatrix}0&0&1\\-1&0&0\\0&-1&0\end{bmatrix}.
\]

即 camera 的前、右、下分别映到 body 的前、右（`-y`）、下（`-z`）。先前若用单位旋转，投影 round trip 仍可为 0，却会把 optical `y` 当 body 横向、把 optical `z` 当 body 高度；这正是为什么必须测试单位轴和完整变换链。

[Modern Robotics](https://modernrobotics.northwestern.edu/nu-gm-book-resource/) 系统讲解刚体运动、齐次变换和 $SE(3)$；本章只提取后续学习系统需要的接口，完整推导交给该开放教材。

### 3.3.1 时间戳也是几何的一部分

若传感器在 $t_s$ 采到本体点 ${}^{body}p$，把它放进世界坐标时需要的是同一采样时刻的位姿：

\[
{}^{world}p(t_s)=T_{world\leftarrow body}(t_s)\,{}^{body}p,
\]

而不是消息到达或融合线程运行时的“最新位姿” $T_{world\leftarrow body}(t_p)$。两者的数组 shape 完全相同，错误却会直接变成空间错位。仅有平移、速度为常数时，错位大小为

\[
\epsilon_{trans}=|v_x|\,|\Delta t|,
\qquad \Delta t=t_p-t_s.
\]

仅有平面转动时，距离旋转中心为 $r$ 的点产生弦长误差

\[
\epsilon_{rot}=2r\sin\left(\frac{|\omega\Delta t|}{2}\right).
\]

| 固定情形 | 点到旋转中心 | 运动 | `sensor_time / pose_time` | 空间误差 |
| --- | ---: | --- | ---: | ---: |
| 仅平移 | 10 m | $v_x=2$ m/s | 1.0 / 0.9 s | 0.20 m |
| 仅转动 | 10 m | $\omega=0.5$ rad/s | 1.0 / 0.9 s | 0.499947918294 m |
| 时间匹配 | 10 m | $v_x=2$ m/s，$\omega=0.5$ rad/s | 1.0 / 1.0 s | 0 m |

*表 3-2：实验 3-1 的解析时间错位夹具。平移和转动行是两个独立对照；不能把两行误差简单相加来近似一般 $SE(3)$ 运动。*<!-- INTERNAL_ASSET_ID: TAB-03-02 -->

真实链路还要分别处理 clock offset、传输/排队延迟、一次扫描或 rolling shutter 内部的采样跨度，以及位姿插值。ROS 2 [`tf2` 时间旅行接口](https://docs.ros.org/en/lyrical/Tutorials/Intermediate/Tf2/Time-Travel-With-Tf2-Cpp.html)显式区分 source time、target time 与 fixed frame；Autoware 的 [point-cloud distortion corrector](https://autowarefoundation.github.io/autoware_universe/pr-10077/sensing/autoware_pointcloud_preprocessor/docs/distortion-corrector/)则按点时间戳结合 twist/IMU 做运动补偿，并把输入同步作为前提。这些接口说明“使用最新 transform”并不等价于“时间已经对齐”；本书没有运行 ROS 或 Autoware，也不据此声称完成真实 deskew。

### 3.3.2 离散 pose 不能直接平均角度

实际 pose 常以离散时间样本到达。查询时刻位于两个样本之间时，至少要预登记：平移如何插值、旋转走哪条弧、最大允许间隔，以及区间外是否允许外推。特别是 yaw 使用 $[-\pi,\pi]$ 表示时，`+170°` 与 `-170°` 在物理上只差 20°；直接算术平均却得到 $0^\circ$，等价于绕长弧经过错误方向。

实验 3-1 v5<!-- INTERNAL_ASSET_ID: EXP-03-01 v5 --> 固定两帧 planar pose：$t=0\ \text{s}$ 时 $(x=0\ \text{m},\ \text{yaw}=+170^\circ)$，$t=1\ \text{s}$ 时 $(x=2\ \text{m},\ \text{yaw}=-170^\circ)$，查询 $t=0.5\ \text{s}$。线性平移与预登记最短 yaw 弧给出 $(x=1\ \text{m},\ \text{yaw}=180^\circ)$；把 yaw 直接平均则得到 $0^\circ$。对 body frame 中 `(10,0,0) m` 的点，两种 world point 相差 20 m。

| 插值规则 | 中点 x | 中点 yaw | 10 m 点相对预登记中点误差 |
| --- | ---: | ---: | ---: |
| 最短角弧 + 线性平移 | 1 m | 180° | 0 m |
| yaw 直接算术平均 | 1 m | 0° | 20 m |

*表 3-3：角度 wrap 的确定性反例。20 m 来自作者构造的 10 m 点和对向角度，不是定位误差分布。*<!-- INTERNAL_ASSET_ID: TAB-03-03 -->

<!-- CLAIM_META: CLAIM-03-10 result -->
实验 3-1 v5<!-- INTERNAL_ASSET_ID: EXP-03-01 v5 --> 的两帧 wrapped-yaw fixture 中，最短角弧插值与预登记中点完全一致，而直接平均 `+170°/-170°` 得到的 world point 相差 20 m；实现同时拒绝无 bracket 的外推和非严格递增时间戳。该结果只验证 planar yaw wrap 与固定点，不证明一般 $SE(3)$ 插值、pose 质量、同步、deskew 或真实车辆误差。

## 3.4 点云、遮挡与简化 BEV

对每个有效深度像素执行反投影，就得到相机坐标点云。点云不是完整世界：它只包含传感器当前能看到且返回有效深度的表面。物体背后、视野外和透明/反光区域应标记为未知，不能默认为空闲。

鸟瞰图（bird's-eye view, BEV）把选定空间范围划分为网格，再将点投影到水平面。最简 occupancy 可以记录每格“有观测占用”，更完整的表示还需要区分 free、occupied、unknown，记录高度、语义、速度和时间。

```mermaid
flowchart TB
    accTitle: FIG-03-02 图 3-2 从二维像素到三维可行动空间
    accDescr: 像素与深度先反投影到相机坐标，再经外参变换到机器人或世界坐标，形成点云、占用和可行动空间；每步保留坐标系、单位和时间。
    R[RGB-D 像素] --> I[内参反投影]
    I --> PC[相机点云]
    PC --> X[外参变换]
    X --> PB[车体/机器人点云]
    PB --> G[栅格化]
    G --> O[occupied/free/unknown]
    O --> V[轴向、尺度、遮挡可视化]
```

*图 3-2：零基础 3D 桥接流水线。每个箭头都保留 frame、unit 和 timestamp；未知空间不能由“没有点”直接推断为空闲。来源：本书原创，CC BY-NC 4.0，2026-08-31。*<!-- INTERNAL_ASSET_ID: FIG-03-02 -->

## 3.5 从关节到末端：只掌握动作接口

二维双连杆机械臂的关节角为 $q=(q_1,q_2)$，连杆长度为 $l_1,l_2$。正运动学把关节状态映射为末端位置：

\[
x=l_1\cos q_1+l_2\cos(q_1+q_2),\quad
y=l_1\sin q_1+l_2\sin(q_1+q_2).
\]

逆运动学反过来寻找达到目标末端位姿的关节配置，可能无解、存在多解或靠近奇异位形。学习策略输出末端位姿时，下层仍需做逆运动学、轨迹生成、碰撞检查和控制；输出关节位置时，也仍需限位、速度和力矩约束。

不同动作空间不能只靠数组长度区分：

| 本体/层级 | 动作示例 | frame 与单位 | 下层责任 |
| --- | --- | --- | --- |
| 机械臂关节 | 目标角/速度/力矩 | joint，rad / rad·s⁻¹ / N·m | 限位、动力学、安全停机 |
| 机械臂末端 | 位姿增量、夹爪开合 | base/tool，m + rad | IK、碰撞、轨迹与力控 |
| 车辆低层 | 转向、加速度、制动 | vehicle，rad / m·s⁻² / ratio | 稳定控制、执行器限制 |
| 车辆规划 | 轨迹点/曲率/速度 | map/vehicle，m / m⁻¹ / m·s⁻¹ | 跟踪器、道路与碰撞约束 |
| 高层技能 | pick、turn-left | task frame，离散 token | 参数化、可行性与终止判断 |

*表 3-4：常见动作接口。策略输出和最终执行器命令之间通常还有不可省略的控制与安全层。*<!-- INTERNAL_ASSET_ID: TAB-03-04 -->

## 3.6 控制频率、延迟与反馈

动作 $a_t$ 的含义依赖控制周期 $\Delta t$。同样的速度命令保持 20 ms 与 200 ms，造成的位移不同；同样 `chunk_size=8`，在 50 Hz 与 5 Hz 系统中分别覆盖 0.16 s 和 1.6 s。频率、保持方式、丢帧和时间戳必须进入实验卡。

开环控制预先生成动作后不根据新观测修正；闭环控制根据误差持续调整。一个最简比例控制器是 $a_t=k(q^*-q_{\text{obs}})$。它不解决动力学、接触或稳定性证明，却足以展示反馈为何能够修正固定执行偏差。

规划器决定较长时域的目标或动作序列，控制器在更高频率上跟踪并抑制扰动；策略可能承担其中任一层。论文中都写 `action`，并不代表动作接口相同。

## 3.7 MDP、POMDP、策略与规划

马尔可夫决策过程（MDP）用状态、动作、转移、奖励和折扣描述序贯决策。若真实状态 $e_t$ 不可完全观测，系统只得到 $o_t$，问题更接近部分可观测 MDP（POMDP）。策略可以基于历史或信念状态：

```text
真实状态 e_t --传感器--> 观测 o_t
历史 (o_≤t, a_<t) --估计/记忆--> 信念 z_t
策略 π(a_t | z_t) --执行--> 环境转移
```

状态是任务相关的理想描述，观测是传感器读数，信念是模型对不可见状态的内部估计。单帧视觉特征不自动满足马尔可夫性：遮挡物体、速度、接触和意图往往需要历史。

策略直接给出动作分布；规划器通常使用模型搜索未来动作序列。工程系统可以用规划器生成参考轨迹、策略提供先验、控制器执行、安全层否决。它们是接口关系，不是互斥阵营。

<!-- CLAIM_META: CLAIM-03-04 fact -->
在部分可观测任务中，单次观测通常不足以等同真实状态；历史或状态估计器用于形成任务相关信念。该定义与第2章术语契约一致。

## 3.8 几何、时间与反馈的四个精确 smoke（实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 -->）

实验完全使用 Python 标准库和程序化 fixture：三个 RGB-D 像素先反投影、变换和栅格化；同一 body 点用匹配/过期位姿变到世界坐标；二维机械臂再比较固定开环增量与带噪观测的比例反馈。

<details markdown="1">
<summary>可选：验证本章证据</summary>

```bash
make ch03-test-local
make ch03-smoke-local
make ch03-smoke
```

</details>

| 检查 | 固定结果 | 应如何解释 |
| --- | ---: | --- |
| 最大投影 round-trip 误差 | 0 px | 精确针孔公式与实现闭合 |
| 最大外参正逆 round-trip 误差 | 8.67×10⁻¹⁸ m | 显式 optical↔body 变换数值闭合 |
| 两段变换顺序执行/组合执行最大差 | 0 m | `world←body←camera` 链的组合实现一致 |
| 毫米误当米的尺度比 | 1000× | 单位错误不会被 shape 检查发现 |
| 外参 x 偏移注入 | 0.10 m | 点云整体系统性平移 |
| 错用单位轴映射的平均点误差 | 2.35718 m | 投影闭合不能检出 frame 轴误用 |
| 离轴 z-depth / 同数值 range 比 | 1.41421× | z-depth 与射线距离不能混用 |
| 2 m/s 平移中的 100 ms 过期位姿 | 0.20 m | 时间偏移可直接成为空间平移误差 |
| 0.5 rad/s 转动中的 100 ms 过期位姿（10 m 点） | 0.49995 m | 转动错位还依赖点到旋转中心的距离 |
| 匹配时间戳的位姿 | 0 m | 固定解析模型的零偏移基线 |
| wrapped yaw 最短角弧插值 | 0 m | 与预登记中点一致 |
| wrapped yaw 直接平均 | 20 m | 角度表示跨 $\pm\pi$ 时走错弧 |
| 固定开环末端误差 | 0.12595 m | 执行偏差逐步累积 |
| 观测反馈末端误差 | 0.01905 m | 在本 fixture 中反馈减小误差 |

*表 3-5：实验 3-1 的固定 CPU smoke。所有数字来自理想程序化模型，不是相机或机器人精度。*<!-- INTERNAL_ASSET_ID: TAB-03-05 -->

<!-- CLAIM_META: CLAIM-03-02 result -->
实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> 的精确针孔 round trip 为 0 px，同时能够检出 1000× 深度尺度错误和 0.10 m 外参平移注入；这只验证理想针孔与手工注入的几何合同，不代表真实标定精度。

<!-- CLAIM_META: CLAIM-03-03 result -->
在同一实验的二维机械臂 fixture 中，固定执行偏差使开环末端误差为 0.12595 m；带确定性观测噪声的比例反馈将其降为 0.01905 m。这个差值只适用于本书固定参数，不能外推实机控制效果。

<!-- CLAIM_META: CLAIM-03-06 result -->
实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> 显式把 optical `(right, down, forward)` 映射到 body `(forward, left, up)`，外参正逆 round trip 最大误差为 8.67×10⁻¹⁸ m；用单位旋转跳过轴映射时，三个点的平均 body 坐标误差为 2.35718 m。该数值只由固定三点和安装平移决定。

<!-- CLAIM_META: CLAIM-03-07 result -->
在归一化离轴坐标 `(1,0)` 上，把数值 1 m 当作 z-depth 得到的射线距离为 1.41421 m；这证明 z-depth 与 range 的接口不可混用，不估计真实深度传感器误差。

<!-- CLAIM_META: CLAIM-03-08 result -->
实验 3-1 v5<!-- INTERNAL_ASSET_ID: EXP-03-01 v5 --> 保留了 v3 的刚体链检查：将 $T_{\text{world_body}}@T_{\text{body_camera}}$ 的组合结果与逐段作用于三个点的结果比较，最大差为 0 m；测试同时拒绝缩放、镜像和剪切矩阵作为 rotation。它验证固定变换实现与输入合同，不证明真实外参或定位正确。

<!-- CLAIM_META: CLAIM-03-09 result -->
实验 3-1 v5<!-- INTERNAL_ASSET_ID: EXP-03-01 v5 --> 在常数 world-x 平移与常数 yaw 的解析夹具中，分别把 100 ms 过期位姿映射为 0.20 m 平移误差，以及 10 m 点上的 0.499947918294 m 转动误差；匹配时间戳时误差为 0 m。这只验证单点、精确时间戳和手工运动参数下的变换合同，不是 localization、pose interpolation、scan deskew、clock synchronization 或真实传感器精度结果。

## 3.9 六类错误的定位顺序

1. **轴向**：单位轴和手系是否符合约定，图像 `v` 向下是否被误当世界 `z`；
2. **单位**：深度、平移、角度、速度和时间分别是什么单位；
3. **刚体性**：rotation 是否满足正交性和 `det=+1`，有没有把缩放、镜像或剪切混进外参；
4. **方向**：保存的是 $T_{\text{target_source}}$ 还是逆变换，矩阵左乘还是右乘；
5. **同步**：RGB、深度、位姿和动作是否属于同一时刻，插值和时钟源是什么；
6. **控制周期**：动作在何时采样、持续多久、是否被限幅或丢弃。

应按这个顺序检查，因为深度模型或策略无法补偿一个稳定但错误的坐标接口。测试必须包含已知原点、单位轴、投影 round trip、正逆变换、时间偏移注入和边界动作。

## 3.10 自动驾驶：相机、车体与地图不能混在一起

自动驾驶至少涉及像素/相机 frame、车辆 body frame、局部里程计 frame 和地图/world frame。相机检测框在像素中，深度或 LiDAR 点在传感器 frame，规划轨迹通常在 vehicle 或 map frame，低层控制再转换为转向、加速度和制动。

本书默认项目必须自行声明轴向；可参考 ROS [REP-103](https://www.ros.org/reps/rep-0103.html) 的单位与坐标约定和 [REP-105](https://www.ros.org/reps/rep-0105.html) 的移动平台 frame 关系，但“参考”不等于所有驾驶数据集和仿真器都使用同一约定。

一个车辆在弯道中移动时，静态相机外参可以保持不变，$T_{\text{map_vehicle}}(t)$ 却随时间变化。将不同时间的点云变到同一地图坐标前必须做运动补偿。错误时间戳可能表现为动态对象拖影或道路边界弯曲，容易被误诊为 3D 模型能力不足。

<!-- CLAIM_META: CLAIM-03-05 recommendation -->
自动驾驶训练与评测应把实际使用的传感器 frame、车辆/map 变换、时间基准和动作持续时间写成数据 schema 的必填字段，并用固定轨迹做变换与同步 smoke；缺失或无法验证的变换不得凭默认值补造，应显式标为无效并排除依赖该字段的样本或任务。

学习策略输出车辆动作时，必须经过道路边界、碰撞、动态约束、控制限幅和最小风险动作；本章程序化几何不构成任何道路安全证据。

## 3.11 全书统一的观测/状态/动作 schema

后续实验至少提供以下机器可读语义，即使具体文件格式不同：

```yaml
observation:
  timestamp_s: float64
  frame_id: camera_front
  modalities: [rgb, depth]
  units: {depth: m}
  calibration_id: fixture-v1
state:
  kind: belief            # true / observed / belief / latent
  frame_id: body
  fields: [joint_position, joint_velocity]
  units: {joint_position: rad, joint_velocity: rad/s}
action:
  kind: joint_position_delta
  frame_id: joint
  units: rad
  control_rate_hz: 20
  horizon_steps: 1
  bounds: [-0.1, 0.1]
  safety_filter: required
episode:
  task_id: string
  reset_id: string
  termination: [success, failure, timeout, safety_stop]
```

`state.kind` 必须区分真实状态、可观测状态、信念和 latent；`action.kind` 必须比 `continuous` 更具体。该 schema 是语义契约，不要求读者现在安装 ROS 或采用某一种数据框架。

## 3.12 4–6 小时桥接门

建议按以下顺序完成：

1. 约 45 min：手算中心像素和边缘像素的反投影；
2. 约 60 min：运行并修改 实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 -->，加入无效深度和单位错误；
3. 约 60 min：画出 camera/body 两组点并检查单位轴与逆变换；
4. 约 45 min：改变 BEV cell size，区分 occupied 与 unknown；
5. 约 60 min：改变控制频率、噪声和执行偏差，比较开环与反馈；
6. 约 30 min：为自己的目标任务填写观测/状态/动作 schema。

通过标准不是记住 $SE(3)$ 定义，而是能在合成数据中定位轴向、单位、外参和时间错误。未通过仍可阅读世界模型或 VLA 主线；进入第12章 occupancy 实验前应补齐此门。

## 3.13 结果、资源、许可与安全边界

| 类型 | 声明/结果 | 来源 | 状态 | 限制 |
| --- | --- | --- | --- | --- |
| 本书结果 | 反投影 round trip 与错误注入可检出 | 实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> | CPU smoke | 三个理想像素 |
| 本书结果 | 过期位姿产生可计算的空间错位 | 实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> | CPU smoke | 单点、常速度/常 yaw 解析模型 |
| 本书结果 | 反馈降低固定二维控制误差 | 实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> | CPU smoke | 无动力学与接触 |
| 开放教材 | $SE(3)$、运动学与操作系统框架 | Modern Robotics / MIT notes | `[O,R1]` | 本书未运行配套栈 |
| 官方规范 | ROS 单位和移动 frame 约定 | REP-103/105 | `[O,R1]` | 数据源可采用不同约定 |

实验下载量 0、无需 GPU、无外部数据或硬件；代码和 fixture 按 MIT 发布，本书原创图按 CC BY-NC 4.0 发布。外部教材和规范保持各自许可，只提供链接，不复制其图表。

真实系统还会受到畸变、滚动快门、深度空洞、温漂、外参变化、clock drift、位姿插值误差、扫描内运动、关节回差、接触、延迟和急停链路影响。S 档 smoke 只证明公式和接口在固定输入上运行，不能证明标定、时间同步、deskew、控制稳定性、实时性或功能安全。

## 小结

从 CV 走向具身系统，关键不是先学完所有机器人学，而是让每个数值带上 frame、unit、timestamp 和控制语义。像素经深度与内参成为相机点，再经外参进入本体/世界；动作经运动学、控制器和安全层改变下一次观测。MDP/POMDP 则把这种反馈和不确定性组织为可学习的决策问题。

## 练习

1. **概念判断**：某点云在相机中单位为毫米，外参平移单位为米，但图形仍像一辆车。为什么可视化不足以证明正确？
2. **代码实验**：给 实验 3-1<!-- INTERNAL_ASSET_ID: EXP-03-01 --> 加入 `5°` yaw 外参错误，比较它与 0.10 m 平移错误的空间模式。
3. **几何练习**：将 body 点变回 camera，验证正逆变换 round trip；再故意把 optical→body 旋转改成单位矩阵，解释为何像素 round trip 仍不报警。
4. **控制练习**：把动作频率从 20 Hz 改为 5 Hz，同时保持每秒速度含义不变；指出代码需要改哪些量。
5. **自动驾驶迁移**：为前视相机、车辆状态和规划轨迹填写本章 schema，并设计一次 100 ms 时间错位注入。
6. **数量级练习**：车辆以 15 m/s 平移时，50 ms 过期位姿会产生多大平移误差？再说明为什么 yaw 造成的误差还需要点的距离才能确定。
7. **插值练习**：解释为什么 `+170°` 与 `-170°` 的算术平均不是物理中点，并写出禁止无 bracket 外推的失败条件。

## 自检要点

先在纸上画 frame 和单位，再展开自检。几何题的“图看起来对”不算验收；至少要检查原点、单位轴、正逆方向、时间和数量级。

<details markdown="1">
<summary>自检 3-1：概念判断</summary>

点之间的相对形状可以在整体尺度错误时保持相似，因此可视化仍像一辆车；但外参的米制平移与毫米点坐标相加会产生 1000 倍语义错配，碰撞距离、速度和地图 cell 都会错误。合格答案应提出数值检查：统一单位后检查已知尺寸、原点/单位轴和 round trip，而不是把渲染外观当标定证据。

</details>

<details markdown="1">
<summary>自检 3-2：代码实验</summary>

0.10 m 平移错误对所有点增加同一个目标-frame 位移向量；5° yaw 错误绕旋转中心转动点，误差方向随方位变化，大小近似随距离 `r` 增长为 $2r\sin(2.5^\circ)$。应冻结同一组三维点，分别注入平移和旋转，报告每点误差而不只报均值，并运行 `make ch03-test-local`。数值只描述固定点集，不能外推真实外参标定精度。

</details>

<details markdown="1">
<summary>自检 3-3：几何练习</summary>

正确检查是 $p_{\text{camera}}\approx T_{\text{camera_body}}@(T_{\text{body_camera}}@p_{\text{camera}})$，同时验证 rotation 正交且 `det=+1`。若 optical→body 错用单位矩阵，而正反投影始终在 camera frame 内使用同一针孔模型，像素 round trip 仍可为 0；错误只在跨 frame 的单位轴语义中出现。合格答案必须解释为何“同一错误用于正反两程”会自洽，并加入 optical right/down/forward 的单位轴测试。

</details>

<details markdown="1">
<summary>自检 3-4：控制练习</summary>

20 Hz 的 $\Delta t=0.05\ \text{s}$，5 Hz 的 $\Delta t=0.2\ \text{s}$。若动作字段表示每步位置增量，为保持同一每秒速度，单步增量应放大 4 倍、每秒步数降为四分之一；若字段本来就是 `m/s`，数值可不变但保持时长和积分必须改。还要复核控制增益、限幅、噪声/延迟的“按步还是按秒”定义，不能只改循环次数。

</details>

<details markdown="1">
<summary>自检 3-5：自动驾驶迁移</summary>

合格 schema 至少让图像带 `sensor_time/camera_front/px` 和 calibration ID，让车辆状态带 `pose_time/vehicle或map frame/m,s,rad`，让轨迹带 reference frame、目标时间、点间隔、速度/曲率和执行 horizon。100 ms 注入应只改变位姿查询时间，保持传感器样本和运动真值固定，再比较匹配/过期变换后的点或轨迹。缺失 transform 时应使依赖样本无效，不能补默认单位矩阵。

</details>

<details markdown="1">
<summary>自检 3-6：数量级练习</summary>

平移误差为 $|v|\cdot|\Delta t|=15\ \text{m/s}\times 0.05\ \text{s}=0.75\ \text{m}$。平面 yaw 误差还取决于角速度和点到旋转中心的距离：弦长为 $2r\sin(|\omega\Delta t|/2)$，同一 yaw 时间差对近点和远点的米制错位不同。只给角度而不给 `r` 不能唯一确定空间误差；一般 SE(3) 运动也不能把独立平移/转动例的标量误差直接相加。

</details>

<details markdown="1">
<summary>自检 3-7：插值练习</summary>

两个角度的坐标表示跨过 $\pm\pi$ 分支切口；应先把角差 wrap 到 $(-\pi,\pi]$，再沿预登记最短弧插值，因此中点是 $\pm180^\circ$ 而不是 $0^\circ$。查询时间早于最早样本、晚于最晚样本、样本时间重复/倒序或时间非有限时都应 fail closed。该规则仍需声明最大 bracket 宽度，且 planar yaw 不能替代一般三维旋转插值。

</details>

## 延伸阅读

- Lynch & Park, [Modern Robotics 在线资源](https://modernrobotics.northwestern.edu/nu-gm-book-resource/)，刚体运动、运动学、规划与控制；
- Tedrake, [Robotic Manipulation: Perception, Planning, and Control](https://manipulation.mit.edu/)，持续更新的开放课程笔记；
- OpenCV, [Camera Calibration 官方文档](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)，相机模型和标定接口；
- ROS, [REP-103](https://www.ros.org/reps/rep-0103.html) 与 [REP-105](https://www.ros.org/reps/rep-0105.html)，单位、坐标与移动平台 frame；
- ROS 2, [tf2：Traveling in time](https://docs.ros.org/en/lyrical/Tutorials/Intermediate/Tf2/Time-Travel-With-Tf2-Cpp.html)，source/target time 与 fixed frame 的显式时间变换；
- Autoware, [Distortion Corrector](https://autowarefoundation.github.io/autoware_universe/pr-10077/sensing/autoware_pointcloud_preprocessor/docs/distortion-corrector/)，按点时间戳与运动信息补偿扫描内畸变；
- Sutton & Barto, [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html)，MDP 与序贯决策的系统教材。

## 下一章接口

第4章将把本章 schema 放进 trajectory、episode、同步和数据切分协议；第12章直接复用反投影、坐标变换和 occupancy 桥接门；第13章的动作块将补上这里定义的单位、频率与安全层接口。
