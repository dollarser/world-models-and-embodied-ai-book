# 编写状态

| 资产 | 状态 | 已验证 | 待验证 |
| --- | --- | --- | --- |
| 执行规格 | `drafted` | 章节、术语、风格、证据、manifest、实验卡、MIT 许可/数据政策、图表和门禁已建立；严格 Schema 检查通过 | benchmark card Schema 与发布门禁扩展 |
| 批次 A：第2、4、6、9章 | `reviewed` | 内容、代码、一致性和教学交叉审查通过，记录见 `reviews/batch-a-review.md` | 各章保留的 GPU/真实数据/上游运行限制 |
| 批次 B（部分通过）：第13、14、15、20章 | `drafted` | 第13–15章四类审查通过；四章共 24 个单元测试与零下载 CPU smoke | 第17、19章已成稿；第20章等待跨批次一致性审查；上游策略/仿真未运行 |
| 批次 C：第3、10、11、12、19章 | `reviewed` | 五章四类审查通过；第5章补齐后关闭第10/11章生成式谱系一致性门 | 真实 3D、视频模型、仿真、数据和 GPU 未运行 |
| 第2章 世界模型到底是什么 | `reviewed` | 正文、8 类四轴系统卡、4 个单元测试与 CPU smoke | 上游逐版本运行核验 |
| 第4章 数据、基线与实验协议 | `reviewed` | 正文、5 类注入错误审计、5 个单元测试与 CPU smoke | 真实数据集审计 |
| EXP-02-01 | `smoke` | 8/8 类别、来源和证据限制记录 | 不是性能 benchmark，未运行上游系统 |
| 第3章 最小机器人学与决策基础 | `reviewed` | 零基础坐标/点云/BEV/运动学/MDP 桥接、动作 schema 与四类审查 | 真实标定、动力学、接触和时间同步 |
| EXP-03-01 | `smoke` | 6 个单元测试；投影、尺度、外参与二维反馈固定结果 | 理想针孔和运动学 fixture，不是实机结果 |
| EXP-04-01 | `smoke` | 有效 fixture 0 问题，5/5 注入问题类型检出 | 未审计真实数据、媒体、标定和隐私 |
| 第5章 预测模型的生成式基础 | `drafted` | VAE/token/自回归/masked/diffusion/flow、自动驾驶多未来与解析 fixture | 神经生成模型、图像/视频、采样性能和 GPU 未运行 |
| EXP-05-01 | `smoke` | 7 个单元测试；点均值落在 support 外，条件 NLL 优于无条件 | 八个标量样本和解析路径，不是生成模型性能 |
| 第9章 世界模型如何评测与失败 | `reviewed` | 正文、指标排序反转 CPU smoke 与自动驾驶评测矩阵 | benchmark card Schema 与上游运行 |
| 第6章正文 | `reviewed` | prior/posterior、自动驾驶正文、资源边界与 CPU smoke 交叉审查 | PyTorch mini-RSSM 与 GPU 验证 |
| EXP-06-01 | `smoke` | 宿主与 Docker CPU 数据流、3 个单元测试、固定指标 | PyTorch 训练、24GB GPU 资源 |
| 第10章 非生成式预测表示 | `reviewed` | 四类审查通过；JEPA 谱系、probe 协议与第5章非生成式边界 | 官方 checkpoint、真实数据与 GPU 未运行 |
| EXP-10-01 | `smoke` | 5 个单元测试；重建与 shifted probe 排名反转 | 手工标量表征，不是 JEPA 性能 |
| 第11章 动作条件视频世界模型 | `reviewed` | 四类审查通过；动作反事实、生成式谱系与 renderer/simulator/planner 边界 | 视频训练、checkpoint、仿真和 GPU 未运行 |
| EXP-11-01 | `smoke` | 6 个单元测试；动作敏感性与未见序列组合 | 确定性网格和 ASCII 帧，不是视频模型 |
| 第12章 可行动的空间表征 | `reviewed` | 3D 零基础入口、三态 occupancy、动态空间、affordance、自动驾驶正文与四类审查 | 真实 RGB-D/驾驶数据、学习模型、仿真和 GPU 均未运行 |
| EXP-12-01 | `smoke` | 7 个单元测试；遮挡未知、坐标偏移、越界与动态路径假安全 | 2D 无噪声射线格子，不是 occupancy 网络或安全证明 |
| 第13章 模仿学习与动作分块 | `reviewed` | 误差累积、动作块延迟、自动驾驶安全时域正文及四类审查 | LeRobot BC/ACT 与 24GB GPU 验证 |
| EXP-13-01 | `smoke` | 0.02 动作偏差在 20 步积分为 0.40；chunk 调用—延迟权衡 | 手工标量 fixture，不是策略性能 |
| 第14章 生成动作 | `reviewed` | 多峰动作、diffusion/flow 最小桥接、采样预算、自动驾驶安全筛选及四类审查 | Push-T/LIBERO、学习策略、GPU 和真实时延均未运行 |
| EXP-14-01 | `smoke` | 7 个单元测试；条件均值无效、refinement 调用—距离权衡 | 解析双峰和 oracle flow，不是方法性能比较 |
| 第15章 VLA 架构模式 | `reviewed` | action token/FAST/连续 expert/双系统、VLM 边界、自动驾驶分层及四类审查 | VLA checkpoint、VLM API、机器人、仿真和 GPU 均未运行 |
| EXP-15-01 | `smoke` | 9 个单元测试；三类动作头统一 schema，5/5 固定错误包被拒绝，另覆盖布尔动作与 horizon 篡改 | 手工移动底盘 packet，不是 VLA 或安全性能 |
| 第16章 数据规模化与跨本体适配 | `drafted` | mixture、canonical action、迁移矩阵、OFT/LoRA/蒸馏和跨车队正文 | 真实数据、learned adapter、迁移实验与 GPU 均未运行 |
| EXP-16-01 | `smoke` | 7 个单元测试；raw pooling MAE 0.28375，schema-aware 为 0 | 两维手工动作，不是 learned transfer 性能 |
| 第17章 世界模型帮助策略的五种方式 | `drafted` | 五类用途、评测替身风险、model exploitation、自动驾驶四角色正文 | learned world model、真实仿真器、上游 checkpoint 与 GPU 均未运行 |
| EXP-17-01 | `smoke` | 6 个单元测试；8/9 转移一致仍造成策略排序反转与碰撞 | 手工 corridor，不是 learned simulator 性能 |
| 第19章 物理仿真、Real2Sim 与 Sim2Real | `reviewed` | 仿真合同、gap 分解、环境矩阵、系统辨识、域随机化、自动驾驶正文与四类审查 | MuJoCo/MetaDrive/CARLA/Isaac、真实系统、资产和 GPU 均未运行 |
| EXP-19-01 | `smoke` | 8 个单元测试；名义 held-out state MAE 0.6625，12 个候选恢复预设参数 | 标量确定性 fixture，不是物理仿真或 Sim2Real 性能 |
| 第20章 具身评测 | `drafted` | 内容、代码、教学审查通过；第17、19章接口已接入 | 批次 C/D 一致性与实际仿真 |
| EXP-20-01 | `smoke` | 同一结果表在两协议下为 100% 与 62.5%，三项差异被检出 | 手工 8 episode，不是 benchmark |
| 第21章 部署、实时性与安全边界 | `drafted` | deadline、尾延迟、异步 chunk、watchdog、fallback 与自动驾驶 MRM 正文 | 真实墙钟、调度器、网络、模型、ROS、硬件和 GPU 未运行 |
| EXP-21-01 | `smoke` | 7 个单元测试；mean 45 ms 掩盖 150 ms 尾部，五类异常分别拒绝 | 手工 latency/packet，不是实时或安全证明 |
| 文档站 | `smoke` | 17 章正文接入 MkDocs Material Docker 严格构建 | 发布部署与浏览器视觉审查 |

状态含义见仓库文件 `specs/PRD/书籍编写与审查执行流程.md`。
