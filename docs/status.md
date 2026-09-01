# 编写状态

| 资产 | 状态 | 已验证 | 待验证 |
| --- | --- | --- | --- |
| 执行规格 | `reviewed` | 章节、术语、证据、manifest、实验卡与 benchmark card、MIT 许可/数据政策、图表和门禁已建立；4 个 Schema 严格检查通过；164 条声明及全部 `FIG/TAB` 双向登记，26 条 `fact` 与8条 `inference` 均有证据合同，75 条 `result` 均绑定同章实验卡并在定义句写明边界 | 机器规则不能判断来源和前提是否真正蕴含文字，也不能替代外部效度、视觉可用性或 benchmark 科学有效性审查 |
| 批次 A：第2、4、6、9章 | `reviewed` | 内容、代码、一致性和教学交叉审查通过，记录见 `reviews/batch-a-review.md` | 各章保留的 GPU/真实数据/上游运行限制 |
| 批次 B：第13、14、15、20章 | `reviewed` | 第13–15章在批次 B 通过；第20章由批次 D 关闭第17/19章一致性门 | 上游策略、仿真、真实数据和 GPU 未运行 |
| 批次 C：第3、10、11、12、19章 | `reviewed` | 五章四类审查通过；第5章补齐后关闭第10/11章生成式谱系一致性门 | 真实 3D、视频模型、仿真、数据和 GPU 未运行 |
| 批次 D：第8、16、17、18、20、21章 | `reviewed` | 六章四类审查通过；40 个单元测试；imagined target—后训练—评测—部署合同闭合 | Dreamer/VLA/world model、仿真、真实系统和 GPU 未运行 |
| 全书终审：第1、5、7、22章 | `reviewed` | 四章内容、代码、一致性和教学审查通过；29 个单元测试；记录见 `reviews/final-book-review.md` | GPU、大数据、真实仿真与硬件限制保持未验证 |
| 快速演进来源审查 | `reviewed` | 第9–11、15、18–21章一手来源复核；修正 WorldArena 2.0/RoboArena 成熟度，确认 KineBench ECCV 2026，补入 Cosmos 3 与 GR00T 四层 horizon | 上游 commit 尚未全部归档；供应商能力和目标环境均未独立验证 |
| 编辑结构与图表无障碍审查 | `reviewed` | 22 章单一 H1、标题不越级；23 张 Mermaid 图加入 `accTitle/accDescr` 并在编译产物保留；未发现 100 字以上整段跨章重复 | 深浅色、窄屏、缩放、键盘与屏幕阅读器仍需人工巡检 |
| 术语与章节接口审查 | `reviewed` | 15 个读者关键缩写/指标同时进入作者基线与读者术语表；6 章合并标题拆为独立教学/接口区段；22 章结构契约自动检查 | 自动覆盖只保证关键项存在，不能替代逐段术语语义、译名偏好和跨学科读者测试 |
| 事实声明来源审查 | `reviewed` | 26 条 `fact` 与机器证据登记双向相等；区分论文、官方资产、供应商声明、本书定义、仓库合同和数学恒等式；3 条方法选择改为 `recommendation` | URL 可访问和登记完整不等于来源蕴含成立；后续仍需周期性人工复核快速演进资产 |
| 推断链与结果解释审查 | `reviewed` | 8 条 `inference` 登记双前提、锚点、反例和范围；1 条采样偏好改为 `recommendation`；75 条 `result` 定义句均有不可外推边界 | 结构化前提不能自动证明推理有效；机制解释与外部效度仍需领域审稿和更强实验 |
| 第1章 从看见到行动 | `reviewed` | 零 3D/RL 入口、闭环地图、三条阅读路线、机器人/自动驾驶双案例与 S 档反例 | 真实感知、控制器、仿真和硬件未运行 |
| EXP-01-01 | `smoke` | 6 个单元测试；相同 MAE、不同积分状态和边界结局 | 标量手工 residual，不是感知、控制或安全性能 |
| 第2章 世界模型到底是什么 | `reviewed` | 8 类四轴卡、三态能力矩阵、VLA/仿真器/学习转移蕴含边界、10 个单元测试与 CPU smoke | 上游逐版本运行核验；教学 archetype 计数不是领域比例 |
| 第4章 数据、基线与实验协议 | `reviewed` | terminated/truncated（含双真边界）、显式缺帧 mask、多传感器 skew、8 类注入错误、14 个单元测试与 CPU smoke | 真实 clock/视频/标定/隐私/许可与数据集审计 |
| EXP-02-01 | `smoke` | 8/8 类别、来源和证据限制；6 张转移证据、5 张动作干预、3 张学习式动作转移、1 张 scope-dependent | 元数据逻辑不是性能、项目比例或上游运行证据 |
| 第3章 最小机器人学与决策基础 | `reviewed` | 零基础 z-depth/range、optical→body 轴映射、点云/BEV/运动学/MDP、动作 schema 与四类审查 | 真实标定、动力学、接触和时间同步 |
| EXP-03-01 | `smoke` | 10 个单元测试；投影、正逆外参、单位轴、深度语义、尺度与二维反馈固定结果 | 理想针孔、固定外参和运动学 fixture，不是实机结果 |
| EXP-04-01 | `smoke` | 有效 fixture 0 问题；8/8 注入问题类型检出；1 terminated + 1 truncated episode；1 个显式 masked sensor sample | 手工 metadata；未审计真实数据、媒体、clock、标定和隐私 |
| 第5章 预测模型的生成式基础 | `reviewed` | VAE/token/自回归/masked/diffusion/flow、五步错误诊断树、aleatoric/epistemic 边界、自动驾驶多未来与解析 fixture；四类审查通过 | 神经生成模型、图像/视频、采样性能和 GPU 未运行 |
| EXP-05-01 | `smoke` | 10 个单元测试；点均值落在 support 外、条件 NLL 优于无条件，并区分条件忽略、mode collapse 与虚构 mode | 八个标量样本；观察 support 不等于真实连续分布 support |
| 第9章 世界模型如何评测与失败 | `reviewed` | one-step/E2/E4 排序反转、逐 horizon attempted/available/coverage、缺失分母反例、自动驾驶矩阵、risk–coverage 协议与 benchmark card | WorldArena/KineBench 等上游未运行，手工缺失惩罚与机器结构不证明外部效度 |
| EXP-09-01 | `smoke` | 9 个单元测试；action sensitivity 0/0.2；fragile 第4步 coverage 1/3，available-case 与固定分母排序相反 | 手工一维预测器和误差表，不是模型崩溃率、自然误差尺度或安全测量 |
| 第6章正文 | `reviewed` | prior/posterior、DreamerV3 dyn/rep stop-gradient 路由、free-nats 日志边界、自动驾驶正文、资源边界与冻结 benchmark card | PyTorch mini-RSSM 与 GPU 验证 |
| EXP-06-01 | `smoke` | 9 个单元测试；固定 filtering/open-loop 指标，以及 raw KL 在 free-nats 阈值两侧的解析诊断 | 不运行自动微分或神经训练，24GB GPU 资源未验证 |
| 第7章 用模型做规划 | `reviewed` | MPC/CEM/tree search/value equivalence、自动驾驶候选轨迹与延迟回报 fixture；四类审查通过 | learned model、CEM/MCTS、仿真、真实回报和 GPU 未运行 |
| EXP-07-01 | `smoke` | 7 个单元测试；H=1/3、terminal value、扰动重规划和受限 Bellman gap | 三状态已知规则，不是 learned planning 性能 |
| 第8章 在想象中学习 | `reviewed` | Dreamer V1–V4 谱系、λ-return、continuation、terminated/truncated bootstrap、误差传播、自动驾驶正文与四类审查 | world model、actor/critic 训练、上游 checkpoint、仿真和 GPU 未运行 |
| EXP-08-01 | `smoke` | 12 个单元测试；λ=0/0.5/1 target、reward bias、终止后泄漏及截断误折叠造成 4 的 bootstrap loss | 标量解析序列，不是 Dreamer、策略改进或样本效率结果 |
| 第10章 非生成式预测表示 | `reviewed` | 四类审查通过；JEPA 2.1 一手资料核验、ID/shift probe 协议、动作接口边界与第5/11章衔接 | 官方 checkpoint、真实数据与 GPU 未运行 |
| EXP-10-01 | `smoke` | 12 个单元测试；重建排名反转、ID 100%→shift 0% 捷径、状态可读但动作盲反事实失败 | 手工标量表征与确定性接口，不是 JEPA、因果或规划性能 |
| 第11章 动作条件视频世界模型 | `reviewed` | 四类审查通过；动作敏感度单位/方向、固定分母 rollout、Cosmos 2.5→3 等开源代际与 renderer/simulator/planner 边界 | 视频训练、checkpoint、仿真和 GPU 未运行 |
| EXP-11-01 | `smoke` | 12 个单元测试；动作盲敏感度归零、左右交换负对照、3 序列/9 转移全轨迹诊断 | 确定性网格和 ASCII 帧，不是视频、因果或规划性能 |
| 第12章 可行动的空间表征 | `reviewed` | 3D 零基础入口、三态 occupancy、动态空间、affordance、自动驾驶正文与四类审查 | 真实 RGB-D/驾驶数据、学习模型、仿真和 GPU 均未运行 |
| EXP-12-01 | `smoke` | 13 个单元测试；遮挡未知、动态清空证据、footprint、观测过期、坐标偏移与输入合同 | 2D 无噪声射线格子和方形 footprint，不是 occupancy 网络、连续碰撞或安全证明 |
| 第13章 模仿学习与动作分块 | `reviewed` | 误差累积、prediction/execution horizon、temporal ensemble 降抖—滞后反例、可执行 chunk 合同、自动驾驶安全时域及四类审查 | LeRobot BC/ACT 与 24GB GPU 验证 |
| EXP-13-01 | `smoke` | 10 个单元测试；0.02 动作偏差积分为 0.40；固定预测时域的 policy query—延迟权衡；时间集成稳态误差 0.001、突变误差 0.754 | 手工标量 fixture，不是策略性能或 ACT 误差率 |
| 第14章 生成动作 | `reviewed` | 多峰动作、diffusion/flow 桥接、候选—batch 预算、独立安全筛选、fallback 与四类审查 | Push-T/LIBERO、学习策略、GPU、真实时延和碰撞器均未运行 |
| EXP-14-01 | `smoke` | 14 个单元测试；条件均值、候选—batch 预算、安全筛选、fallback 与输入合同 | 解析双峰、抽象 forward 和手工门禁，不是方法、时延或安全性能比较 |
| 第15章 VLA 架构模式 | `reviewed` | action token/FAST/连续 expert/双系统、模型容量—数据窗口—输出—执行四层 horizon、异步命令身份、VLM 边界与自动驾驶分层 | VLA checkpoint、VLM API、认证、机器人、仿真和 GPU 均未运行 |
| EXP-15-01 | `smoke` | 15 个单元测试；三类动作头统一 schema，10/10 错误包被拒绝，覆盖 horizon 越权、replay、乱序、clock 与字段顺序 | 手工单会话移动底盘 packet，不是 VLA、网络安全或功能安全性能 |
| 第16章 数据规模化与跨本体适配 | `reviewed` | mixture、四类动作统一路线、版本化 adapter/统计量、seen/few-shot/zero-shot 迁移矩阵、OFT/LoRA/蒸馏、跨车队正文与四类审查 | 真实数据、learned adapter、迁移实验与 GPU 均未运行 |
| EXP-16-01 | `smoke` | 12 个单元测试；raw pooling MAE 0.28375，schema-aware 为 0，3/3 合同错误拒绝且语义变化改变 fingerprint | 两维手工动作；fingerprint 不是安全签名，不是 learned transfer 性能 |
| 第17章 世界模型帮助策略的五种方式 | `reviewed` | 五类非互斥用途、代理评测三段误差、model exploitation、coverage gate、自动驾驶四角色正文与四类审查 | learned world model、真实仿真器、上游 checkpoint 与 GPU 均未运行 |
| EXP-17-01 | `smoke` | 10 个单元测试；8/9 转移一致仍造成错排与碰撞；support gate 拒绝 support 外捷径并把 regret 1.85→0 | 手工 corridor/oracle support，不是 learned OOD 或 simulator 性能 |
| 第18章 VLA 后训练与 WAM | `reviewed` | 五类后训练、RLOO 退化/重采样分母、联合轨迹支持、长时层级/记忆、WAM 四类接口、自动驾驶正文与四类审查 | VLA/RL/world model、LIBERO、仿真、GPU 和硬件未运行 |
| EXP-18-01 | `smoke` | 11 个单元测试；reward target/ESS/recovery；marginal gate 错收未见组合；全同 reward 零 LOO 信号 | 四条标量轨迹与手工阈值，不是 offline RL、learned support 或 policy 改进 |
| 第19章 物理仿真、Real2Sim 与 Sim2Real | `reviewed` | 仿真合同、gap 分解、结构/实用可辨识性、MuJoCo sysid、联合随机化边界、自动驾驶正文与四类审查 | MuJoCo/MetaDrive/CARLA/Isaac、真实系统、资产和 GPU 均未运行 |
| EXP-19-01 | `smoke` | 10 个单元测试；observation-only 有 2 个零误差解；等价解隐藏 state MAE 0.1625；state anchor 后唯一 | 标量无噪网格，不是物理仿真、真实参数辨识或 Sim2Real 性能 |
| 第20章 具身评测 | `reviewed` | 四类审查通过；证据层级、协议交互、泄漏/盲法、cluster/paired/macro-micro 统计、CARLA 2.1 与机器 benchmark card 已接入 | 真实 clustered interval、真机/仿真与外部评测网络 |
| EXP-20-01 | `smoke` | 14 个单元测试；四格协议为 100%/100%/87.5%/62.5%，interaction -25pp；8 attempted/8 valid/7 terminated/1 truncated/0 invalid | 手工 8 episode、独立 Bernoulli 假设；算术对照不是 benchmark、因果效应或故障率估计 |
| 第21章 部署、实时性与安全边界 | `reviewed` | deadline burst、异步 chunk 新鲜度/underflow、watchdog、版本化 uncertainty gate、迟滞 fallback、Autoware MRM 状态与四类审查 | 真实墙钟、校准 estimator、调度器、网络、模型、ROS、执行器、硬件和 GPU 未运行 |
| EXP-21-01 | `smoke` | 14 个单元测试；mean 45 ms 掩盖尾部；同 miss rate 的 burst 长度 2/1；8 步 schedule 有 1 stale/1 underflow；3-failure/2-health 状态机 | 手工 latency/packet/score/chunk/状态，不是实时、OOD、MRM 可达性或安全证明 |
| 第22章 可审计综合项目 | `reviewed` | 可证伪问题、五条选题轨道、五段跨章证据 trace、交付物、阶段提交、驾驶合同与研究雷达已接入正文；四类审查通过 | 模型、数据、仿真、GPU、机器人、车辆与部署均未运行 |
| EXP-22-01 | `smoke` | 12 个单元测试；完整包 5 段 trace/0 issue，无效包 16 个具名 issue，缺段与错误依赖被拒绝 | metadata 图检查，不验证 artifact 内容、科学正确性或安全性 |
| 文档站 | `release-candidate` | 22 章正文、读者术语表、22 张实验卡、3 张 benchmark card、256 个章节单元测试、22 组结果精确比对、27 个 HTML/23 张可访问 Mermaid 图/1009 个内部目标检查、本地静态预览与 MkDocs 严格构建 | 尚未部署；截图式多尺寸、深浅色、键盘与屏幕阅读器巡检仍待人工确认 |

状态含义见仓库文件 `specs/PRD/书籍编写与审查执行流程.md`。
