# 编写状态

| 资产 | 状态 | 已验证 | 待验证 |
| --- | --- | --- | --- |
| 执行规格 | `drafted` | 章节、术语、风格、证据、manifest、实验卡、MIT 许可/数据政策、图表和门禁已建立；严格 Schema 检查通过 | benchmark card Schema 与发布门禁扩展 |
| 批次 A：第2、4、6、9章 | `reviewed` | 内容、代码、一致性和教学交叉审查通过，记录见 `reviews/batch-a-review.md` | 各章保留的 GPU/真实数据/上游运行限制 |
| 批次 B（进行中）：第13、20章 | `drafted` | 两章正文、各 4 个单元测试与零下载 CPU smoke | 等待前置章节后做一致性审查；上游策略/仿真未运行 |
| 第2章 世界模型到底是什么 | `reviewed` | 正文、8 类四轴系统卡、4 个单元测试与 CPU smoke | 上游逐版本运行核验 |
| 第4章 数据、基线与实验协议 | `reviewed` | 正文、5 类注入错误审计、5 个单元测试与 CPU smoke | 真实数据集审计 |
| EXP-02-01 | `smoke` | 8/8 类别、来源和证据限制记录 | 不是性能 benchmark，未运行上游系统 |
| EXP-04-01 | `smoke` | 有效 fixture 0 问题，5/5 注入问题类型检出 | 未审计真实数据、媒体、标定和隐私 |
| 第9章 世界模型如何评测与失败 | `reviewed` | 正文、指标排序反转 CPU smoke 与自动驾驶评测矩阵 | benchmark card Schema 与上游运行 |
| 第6章正文 | `reviewed` | prior/posterior、自动驾驶正文、资源边界与 CPU smoke 交叉审查 | PyTorch mini-RSSM 与 GPU 验证 |
| EXP-06-01 | `smoke` | 宿主与 Docker CPU 数据流、3 个单元测试、固定指标 | PyTorch 训练、24GB GPU 资源 |
| 第13章 模仿学习与动作分块 | `drafted` | 误差累积、动作块延迟、自动驾驶安全时域正文 | LeRobot BC/ACT 与 24GB GPU 验证 |
| EXP-13-01 | `smoke` | 0.02 动作偏差在 20 步积分为 0.40；chunk 调用—延迟权衡 | 手工标量 fixture，不是策略性能 |
| 第20章 具身评测 | `drafted` | 协议可比性、证据阶梯、自动驾驶指标正文 | 第15/17/19章接口与实际仿真 |
| EXP-20-01 | `smoke` | 同一结果表在两协议下为 100% 与 62.5%，三项差异被检出 | 手工 8 episode，不是 benchmark |
| 文档站 | `smoke` | 6 章正文接入 MkDocs Material Docker 严格构建 | 发布部署与浏览器视觉审查 |

状态含义见仓库文件 `specs/PRD/书籍编写与审查执行流程.md`。
