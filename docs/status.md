# 编写状态

| 资产 | 状态 | 已验证 | 待验证 |
| --- | --- | --- | --- |
| 执行规格 | `reviewed` | 章节、术语、证据、manifest、实验卡与 benchmark card、MIT 许可/数据政策、图表和门禁已建立；4 个 Schema、68 项严格规格测试通过；PRD 22 章均把当前 `EXP-NN-01` S 档与可选 M/L 路径分开，22 个实验资产包具有 README、实验卡、可测试源码、smoke、测试和中央结果；197 条声明及全部 `FIG/TAB` 双向登记，29 条 `fact` 与 8 条 `inference` 均有证据合同，105 条 `result` 均绑定同章实验卡并在定义句写明边界，55 条 `recommendation` 中 24 条高后果建议登记适用条件、停止路径与未授权事项；全部 Markdown 审查记录必须可从审查索引发现 | 机器规则不能判断来源和前提是否真正蕴含文字，也不能替代关键建议选择是否完备、外部效度、视觉可用性或 benchmark 科学有效性审查 |
| 批次 A：第2、4、6、9章 | `reviewed` | 内容、代码、一致性和教学交叉审查通过，记录见 `reviews/batch-a-review.md` | 各章保留的 GPU/真实数据/上游运行限制 |
| 批次 B：第13、14、15、20章 | `reviewed` | 第13–15章在批次 B 通过；第20章由批次 D 关闭第17/19章一致性门 | 上游策略、仿真、真实数据和 GPU 未运行 |
| 批次 C：第3、10、11、12、19章 | `reviewed` | 五章四类审查通过；第5章补齐后关闭第10/11章生成式谱系一致性门 | 真实 3D、视频模型、仿真、数据和 GPU 未运行 |
| 批次 D：第8、16、17、18、20、21章 | `reviewed` | 六章四类审查通过；40 个单元测试；imagined target—后训练—评测—部署合同闭合 | Dreamer/VLA/world model、仿真、真实系统和 GPU 未运行 |
| 全书终审：第1、5、7、22章 | `reviewed` | 四章内容、代码、一致性和教学审查通过；29 个单元测试；记录见 `reviews/final-book-review.md` | GPU、大数据、真实仿真与硬件限制保持未验证 |
| 快速演进来源审查 | `reviewed` | 第4、9–19、21章一手来源分批复核；支持正式 `fact`、`inference` 前提的 GitHub 实现、研究雷达官方仓库及当前读者文档的具体 GitHub 文件/目录均锁完整 commit；原有14个 `blob/tree main/master` 浮动链接清零；第18章新增 World-Gymnast、WMPO、WAM taxonomy 与 SimWAM 实现快照 | 仓库落地页仍只作发现入口；其他外部页面、论文修订、供应商能力和目标环境需周期复核，锁定源码不等于执行或独立验证 |
| 快速演进研究雷达 | `reviewed` | 12 张一手来源活页卡按问题、章节、source revision、资产开放度、复现状态、资源路径、范围边界和复核触发器登记；V-JEPA 2.1、Cosmos 3、POBAX 与 A2World 仓库已锁不可变 commit；新增XEWorld受控跨本体反例、Riemann-1.0统一WAM监测项，A2World双用途证据设计已进入第17章 | 当前只完成论文/官方资产审计和无下载预检；模型、权重、数据、GPU、仿真与真实系统均未运行，扩展仓库仍按需逐批锁定 |
| 编辑结构与图表无障碍审查 | `reviewed` | 29个编译页面均自动验证中文语言、device-width viewport、唯一main/H1和图片alt；28个正文页面验证有效skip link，短404页明确豁免；22章标题不越级；23张Mermaid图保留`accTitle/accDescr` | 浏览器控制接口当前不可用；深浅色、窄屏、缩放、键盘焦点顺序与屏幕阅读器朗读仍需人工巡检，不由DOM门禁替代 |
| 术语与章节接口审查 | `reviewed` | 15 个读者关键缩写/指标同时进入作者基线与读者术语表；6 章合并标题拆为独立教学/接口区段；22 章结构契约自动检查 | 自动覆盖只保证关键项存在，不能替代逐段术语语义、译名偏好和跨学科读者测试 |
| 贯穿案例与概念递进审查 | `reviewed` | 杯子操作与施工改道两个固定任务串联22章；对 observation/state/action/prediction/horizon/success/uncertainty 给出逐层证据升级表，并提供无3D经验与自动驾驶阅读路径 | 贯穿任务是教学索引，不是共享数据集或端到端实验；仍需真实读者测试跳转密度与理解负担 |
| 练习与自学出口审查 | `reviewed` | 22 章 127 道练习均有折叠式同编号自检要点；全部容器启用 Markdown-in-HTML，编译门禁拒绝原始反引号残留；manifest 登记全章覆盖，源码门禁拒绝缺失、重复、跨章、顺序错位、未闭合和过短答案 | 自检是最低合格要点，不是开放题唯一答案或真实实验替代品；仍需真实读者测试难度、歧义与真实屏幕阅读器体验 |
| 事实声明来源审查 | `reviewed` | 29 条 `fact` 与机器证据登记双向相等；GitHub `official_asset` 全部使用 40 位 commit URL；区分论文、官方资产、供应商声明、本书定义、仓库合同和数学恒等式 | 不可变 URL 只固定被审查内容，不证明来源蕴含、独立复现或当前上游默认行为；仍需周期性人工复核 |
| 推断链与结果解释审查 | `reviewed` | 8 条 `inference` 登记双前提、锚点、反例和范围；GitHub 实现前提必须锁完整 commit；1 条采样偏好改为 `recommendation`；105 条 `result` 定义句均有不可外推边界 | 结构化前提不能自动证明推理有效；机制解释与外部效度仍需领域审稿和更强实验 |
| 关键建议适用性审查 | `reviewed` | 24 条资源升级、数据纳入、评测发布、运行激活或安全执行建议登记 trigger、动作、fallback/stop 与未授权事项；8 条正文补齐失败路径 | 自动规则不能保证高后果建议选择已穷尽，也不构成硬件、数据、机器人或车辆授权 |
| PRD 实验档位一致性审查 | `reviewed` | 22 章逐一绑定当前 S 档 `EXP-NN-01`，并把训练、真实数据、checkpoint 与仿真拆为可选待验证 M/L 路径；当前仓库树与脚本名已同步 | 只证明设计—交付映射正确，不表示任何 M/L 路径已经运行或资源可复现 |
| 实验资产最小合同审查 | `reviewed` | 22 个 manifest 实验与实验卡双向一致，并具有 README、可测试 `src`、smoke、测试和存在的结果 artifact；解析 fixture 不再被要求伪造训练/config 步骤 | 资产完整和 S 档通过不证明训练、外部数据、仿真或目标硬件可复现 |
| 第1章 从看见到行动 | `reviewed` | 零 3D/RL 入口、闭环地图、三条阅读路线、机器人/自动驾驶双案例，以及反馈—时延—动作权限 S 档反例 | 真实感知、控制器、仿真和硬件未运行 |
| EXP-01-01 | `smoke` | 10 个单元测试；相同 MAE 的不同积分结局，以及及时反馈、两步时延和动作限幅的固定结果 | 无单位标量 fixture，不是感知、物理控制器或安全性能 |
| 第2章 世界模型到底是什么 | `reviewed` | 8 类四轴卡、三态能力矩阵、state-aliasing/history gap、VLA/仿真器/学习转移蕴含边界、14 个单元测试与 CPU smoke | 上游逐版本运行核验；教学 archetype 和两 context 不是领域比例或 learned-memory 性能 |
| 第4章 数据、基线与实验协议 | `reviewed` | terminated/truncated（含双真边界）、显式缺帧 mask、多传感器 skew、group/来源/精确内容/近重复簇四层身份边界、11 类注入错误、18 个单元测试与 CPU smoke | 真实 clock/视频/标定/隐私/许可，以及 perceptual/embedding 近重复检索与数据集审计 |
| EXP-02-01 | `smoke` | 8/8 类别、来源和证据限制；6 张转移证据、5 张动作干预、3 张学习式动作转移；current-only/history-aware mean return 为 0.1/0.6 | 元数据与两 context oracle 不是项目比例、POMDP solver、learned memory 或上游性能 |
| 第3章 最小机器人学与决策基础 | `reviewed` | 零基础 z-depth/range、optical→body 轴映射、时变位姿错位、点云/BEV/运动学/MDP、动作 schema 与四类审查 | 真实标定、定位、pose interpolation、scan deskew、动力学、接触和 clock synchronization |
| EXP-03-01 | `smoke` | 16 个单元测试；投影、正逆外参、单位轴、深度语义、尺度、100 ms 位姿错位与二维反馈固定结果 | 理想针孔、单点常运动、固定外参和运动学 fixture，不是实机或时间同步结果 |
| EXP-04-01 | `smoke` | 有效 fixture 0 问题；11/11 注入问题类型检出，其中 1 个 group 与 3 个独立身份重叠；1 terminated + 1 truncated episode；1 个显式 masked sensor sample | 手工 metadata ID；未读取媒体、发现未知近重复或审计真实数据、clock、标定和隐私 |
| 第5章 预测模型的生成式基础 | `reviewed` | VAE/token/自回归/masked/diffusion/flow、五步错误诊断树、aleatoric/epistemic 边界、ensemble correlated-error 反例、自动驾驶多未来与解析 fixture；四类审查通过 | 神经生成模型、learned ensemble/OOD estimator、图像/视频、采样性能和 GPU 未运行 |
| EXP-05-01 | `smoke` | 14 个单元测试；点均值落在 support 外、条件 NLL 优于无条件，区分条件忽略/mode collapse/虚构 mode，并证明共同错误可在 range 0 时漏过门禁 | 八个分布样本与三个手写成员；观察 support 不等于真实连续 support，range 不是校准或 OOD 保证 |
| 第9章 世界模型如何评测与失败 | `reviewed` | one-step/E2/E4 排序反转、逐 horizon attempted/available/coverage、缺失分母反例、proper probability score 与分箱 ECE 负对照、自动驾驶矩阵、risk–coverage 协议与 benchmark card | WorldArena/KineBench 等上游未运行；手工概率/缺失表与机器结构不证明总体校准、uncertainty 或外部效度 |
| EXP-09-01 | `smoke` | 12 个单元测试；action sensitivity 0/0.2；fragile 第4步 coverage 1/3，available-case 与固定分母排序相反；两 forecast 单 bin ECE 同为0但 Brier 为0.25/0.01 | 手工一维预测器、误差表与4个二元结果，不是模型崩溃率、总体校准、自然误差尺度或安全测量 |
| 第6章正文 | `reviewed` | prior/posterior、DreamerV3 dyn/rep stop-gradient 路由、free-nats 日志边界、自动驾驶正文、资源边界；`BENCH-06-01` v2 已把31个 rollout 转移与两组 KL 阈值/scale/目标标签统一冻结 | PyTorch mini-RSSM、真实自动微分梯度与 GPU 验证 |
| EXP-06-01 | `smoke` | 9 个单元测试；固定 filtering/open-loop 指标，以及 raw KL 在 free-nats 阈值两侧的解析诊断 | 不运行自动微分或神经训练，24GB GPU 资源未验证 |
| 第7章 用模型做规划 | `reviewed` | MPC/CEM/tree search/value equivalence、PETS 粒子传播接口、固定动作预算的扰动重规划、环境 reward/terminal value 分账、风险目标排序反例、非整数经验尾部质量审计与自动驾驶正文；四类审查通过 | learned probabilistic model、总体 CVaR/置信区间、概率校准、CEM/MCTS、仿真、真实回报和 GPU 未运行 |
| EXP-07-01 | `smoke` | 13 个单元测试；H=1/3、terminal value、扰动协议负对照、固定两动作槽的 reward-only/bootstrapped objective、受限 Bellman gap 与风险排序反转 | 三状态已知规则、一个固定扰动和五个手工等权场景；不是 learned planning、真实概率或安全性能 |
| 第8章 在想象中学习 | `reviewed` | Dreamer V1–V4 谱系、λ-return、continuation target/累计 loss weight、terminated/truncated bootstrap、截断 bootstrap 与跨 episode λ-trace 分离、误差传播、自动驾驶正文与四类审查 | world model、actor/critic 训练、learned continuation、真实 replay 污染率、上游 checkpoint、仿真和 GPU 未运行 |
| EXP-08-01 | `smoke` | 18 个单元测试；λ=0/0.5/1 target、reward bias、终止后泄漏、截断误折叠造成4的 bootstrap loss、遗漏 trace 边界造成96的跨 episode leakage，以及 post-terminal loss leakage 100 | 标量解析序列，不是 Dreamer、梯度、策略改进、replay 污染率或样本效率结果 |
| 第10章 非生成式预测表示 | `reviewed` | 四类审查通过；V-JEPA 2.1 一手资料核验、ID/shift probe 协议、动作接口边界与第5/11章衔接；锁定快照的默认 Hub URL 指向 localhost 已登记为 S1 阻塞而非可运行证据 | 官方 checkpoint、真实数据与 GPU 未运行；需先锁定兼容 loader/权重与校验和 |
| EXP-10-01 | `smoke` | 12 个单元测试；重建排名反转、ID 100%→shift 0% 捷径、状态可读但动作盲反事实失败 | 手工标量表征与确定性接口，不是 JEPA、因果或规划性能 |
| 第11章 动作条件视频世界模型 | `reviewed` | 四类审查通过；动作敏感度单位/方向、固定分母 rollout、Cosmos 2.5→3 等开源代际与 renderer/simulator/planner 边界 | 视频训练、checkpoint、仿真和 GPU 未运行 |
| EXP-11-01 | `smoke` | 12 个单元测试；动作盲敏感度归零、左右交换负对照、3 序列/9 转移全轨迹诊断 | 确定性网格和 ASCII 帧，不是视频、因果或规划性能 |
| 第12章 可行动的空间表征 | `reviewed` | 3D 零基础入口、米制点→半开栅格边界、三态 occupancy、动态空间、稀疏 waypoint 路径段、affordance、四类 occupancy 任务边界、自动驾驶正文与四类审查 | 真实 RGB-D/驾驶数据、外部地图、continuous collision、学习模型、仿真和 GPU 均未运行 |
| EXP-12-01 | `smoke` | 19 个单元测试；半开米制栅格边界、遮挡未知、动态清空证据、Bresenham 路径段、footprint、观测过期、坐标偏移与输入合同 | 固定 2D 无噪声射线格、整数中心线和方形 footprint，不是外部地图、occupancy 网络、连续碰撞或安全证明 |
| 第13章 模仿学习与动作分块 | `reviewed` | 误差累积、prediction/execution horizon、temporal ensemble 降抖—滞后反例、可执行 chunk 合同、自动驾驶安全时域及四类审查 | LeRobot BC/ACT 与 24GB GPU 验证 |
| EXP-13-01 | `smoke` | 13 个单元测试；相同 0.02 RMSE/MAE 的持续/交替误差产生 0.40/0 的最终积分偏差；固定预测时域的 policy query—延迟权衡；时间集成稳态误差 0.001、突变误差 0.754 | 无反馈手工标量 fixture，不是闭环策略性能或 ACT 误差率 |
| 第14章 生成动作 | `reviewed` | 多峰动作、diffusion/flow 桥接、模式覆盖—频率负对照、候选—batch 预算、独立安全筛选、fallback 与四类审查 | Push-T/LIBERO、学习策略、总体校准、GPU、真实时延和碰撞器均未运行 |
| EXP-14-01 | `smoke` | 17 个单元测试；条件均值；相同有效率/覆盖下经验频率 TV 0/0.4；候选—batch 预算、安全筛选、fallback 与输入合同 | 解析双峰、10个手工样本、抽象 forward 和手工门禁，不是方法、总体概率、时延或安全性能比较 |
| 第15章 VLA 架构模式 | `reviewed` | action token/FAST/连续 expert/双系统、模型容量—数据窗口—输出—执行四层 horizon、异步观测/动作 timestep 与命令身份、VLM 边界和自动驾驶分层 | VLA checkpoint、真实异步队列、VLM API、认证、机器人、仿真和 GPU 均未运行 |
| EXP-15-01 | `smoke` | 18 个单元测试；三类动作头统一 schema，12/12 错误包被拒绝，覆盖 horizon 越权、墙钟新鲜但 step 错位、replay、乱序、clock 与字段顺序 | 手工单会话移动底盘 packet 和固定42调度槽，不是 VLA、时钟同步、网络安全或功能安全性能 |
| 第16章 数据规模化与跨本体适配 | `reviewed` | mixture、四类动作统一路线、版本化 adapter/统计量、seen/few-shot/zero-shot 迁移矩阵，以及 XEWorld 的本体留出、四轴归因与适配遗忘案例；OFT/LoRA/蒸馏、跨车队正文与四类审查 | XEWorld 只审计论文协议；真实数据、模型、learned adapter、迁移实验与 GPU 均未运行 |
| EXP-16-01 | `smoke` | 12 个单元测试；raw pooling MAE 0.28375，schema-aware 为 0，3/3 合同错误拒绝且语义变化改变 fingerprint | 两维手工动作；fingerprint 不是安全签名，不是 learned transfer 性能 |
| 第17章 世界模型帮助策略的五种方式 | `reviewed` | 五类非互斥用途、代理评测四段归因账、prospective policy split、model exploitation、coverage 外拒绝与 coverage 内错误负对照；A2World 案例要求共享先验的 simulator/policy 分支独立验收 | learned world model、真实新策略、A2World-policy、真实仿真器、上游 checkpoint 与 GPU 均未运行；上游全量微调示例超出默认资源档位 |
| EXP-17-01 | `smoke` | 19 个单元测试；两策略 calibration 的 `ρ=1/gap=0` 在加入 held-out shortcut 后变为 `ρ=-0.5/regret=1.85`；另覆盖 support gate 与四段归因不可辨识反例 | 三个手工策略、authored split/support 与单故障组件注入，不是 learned policy 泛化率、故障率、可加总误差预算或 simulator 性能 |
| 第18章 VLA 后训练与 WAM | `reviewed` | 五类后训练、RLOO 退化与 dynamic rejection 的 attempted/rejected/used 分母、联合轨迹支持、长时层级/记忆、WAM 四类接口；SimWAM attention/deployment 源码边界与 World-Gymnast/WMPO 资源预检已锁定，自动驾驶正文与四类审查通过 | VLA/RL/world model、LIBERO、仿真、GPU 和硬件未运行；World-Gymnast 默认四卡且含宿主缓存清理，WMPO 整包资产禁止默认下载 |
| EXP-18-01 | `smoke` | 14 个单元测试；reward target/ESS/recovery；marginal gate 错收未见组合；全同 reward 零 LOO 信号；dynamic rejection 改变 used context 分布 | 四条标量轨迹和四个手工 context 组，不是 offline RL、learned support、真实采样率或 policy 改进 |
| 第19章 物理仿真、Real2Sim 与 Sim2Real | `reviewed` | 仿真合同、gap 分解、结构/实用可辨识性、MuJoCo sysid、联合随机化边界、自动驾驶正文与四类审查 | MuJoCo/MetaDrive/CARLA/Isaac、真实系统、资产和 GPU 均未运行 |
| EXP-19-01 | `smoke` | 10 个单元测试；observation-only 有 2 个零误差解；等价解隐藏 state MAE 0.1625；state anchor 后唯一 | 标量无噪网格，不是物理仿真、真实参数辨识或 Sim2Real 性能 |
| 第20章 具身评测 | `reviewed` | 四类审查通过；证据层级、协议交互、checkpoint final-set reuse、泄漏/盲法、cluster/paired/macro-micro、同边际 joint-pairing 统计、零安全事件上界与 pseudo-replication 分析单位反例、CARLA 2.1 与机器 benchmark card 已接入 | 真实 adaptive-selection history、matched effect interval、clustered interval、cluster 内相关性、multiplicity/adaptivity、真机/仿真与外部评测网络；手工 exact/selection 数值不估计策略效应或期望偏差，零事件公式不覆盖漏检、未见危险或 ODD/sim-to-real shift |
| EXP-20-01 | `smoke` | 29 个单元测试；四格协议 interaction -25pp；8 attempted/8 valid/7 terminated/1 truncated；10 对结果的 episode-micro 差 +0.3、等 route macro 差 0、四 cluster 枚举区间 [-0.75,0.75]；两张20对表同为0.6/0.4与+0.2，但 discordant 4:0/8:4、exact conditional p为0.125/0.387695；零事件 `0/100` episode-iid 与 `0/10` route-incidence 上界为2.9513%/25.8866%；final-set reuse 负对照的 authored gap 为0.25 | 手工 8 episode + 10 对/4 route + 两张20对 joint table + 4 checkpoint×3 split + 10 route×10 replay 与解析二项式；paired p、selection gap 与零事件上界都不是策略、效应区间、有效样本量、等效性、部署风险或 population inference |
| 第21章 部署、实时性与安全边界 | `reviewed` | deadline burst、异步 chunk 新鲜度/underflow、watchdog、版本化 uncertainty gate、严重度分层负对照、迟滞 fallback、健康/完成/失败/授权分离、绑定及时效化 receipt、Autoware MRM 与过渡超时语义以及四类审查 | 真实墙钟、校准 estimator、真实严重度/暴露量/后果、调度器、网络、模型、ROS、执行器、完成检查器、身份认证/完整性、实际授权链、备用 MRM 切换、硬件和 GPU 未运行 |
| EXP-21-01 | `smoke` | 26 个单元测试；mean 45 ms 掩盖尾部；同 miss rate 的 burst 长度 2/1；8 步 schedule 有 1 stale/1 underflow；相同失败计数下接受 authored weight 1/10；健康仅/授权感知重新激活；成功第 2 步/授权第 3 步、超时与失败锁定；9 个 receipt 中 1 允许/8 拒绝 | 手工 latency/packet/score/代理权重/chunk/状态/授权/receipt，不是实时、OOD、真实后果、MRM 完成、认证授权、完整性、备用 MRM 切换或安全证明 |
| 第22章 可审计综合项目 | `reviewed` | 可证伪问题、五条选题轨道、五段跨章证据 trace、三分区 × 四身份数据隔离、交付物、阶段提交、驾驶合同与研究雷达已接入正文；四类审查通过 | 模型、真实数据/媒体、仿真、GPU、机器人、车辆与部署均未运行；未发现未知近重复 |
| EXP-22-01 | `smoke` | 23 个单元测试；完整包 12 个 split identity set/5 段 trace/5 个 artifact binding/2 个 failure injection/0 issue，无效包 23 个具名 issue，四类 train–eval 重叠、缺段、错误依赖、评测未冻结与缺失安全网关均被拒绝 | metadata 图检查，不读取媒体、发现未知近重复或验证 artifact 内容、科学正确性与安全性 |
| 文档站 | `release-candidate` | 22 章正文、读者术语表、研究雷达、贯穿案例阅读地图、22 张实验卡、3 张 benchmark card、351 个章节单元测试、22 组结果精确比对、29 个 HTML/23 张可访问 Mermaid 图/127 个已渲染 Markdown 的折叠式练习自检/1161 个内部目标检查、本地静态预览与 MkDocs 严格构建 | 尚未部署；截图式多尺寸、深浅色、键盘与屏幕阅读器巡检仍待人工确认，自动 DOM 检查不替代视觉与辅助技术验收 |

状态含义见仓库文件 `specs/PRD/书籍编写与审查执行流程.md`。
