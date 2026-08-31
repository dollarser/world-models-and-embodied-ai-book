# 编写状态

| 资产 | 状态 | 已验证 | 待验证 |
| --- | --- | --- | --- |
| 执行规格 | `drafted` | 章节、术语、风格、证据、manifest、实验卡、MIT 许可/数据政策、图表和门禁已建立；严格 Schema 检查通过 | benchmark card Schema 与发布门禁扩展 |
| 批次 A：第2、4、6、9章 | `reviewed` | 内容、代码、一致性和教学交叉审查通过，记录见 `reviews/batch-a-review.md` | 各章保留的 GPU/真实数据/上游运行限制 |
| 第2章 世界模型到底是什么 | `reviewed` | 正文、8 类四轴系统卡、4 个单元测试与 CPU smoke | 上游逐版本运行核验 |
| 第4章 数据、基线与实验协议 | `reviewed` | 正文、5 类注入错误审计、5 个单元测试与 CPU smoke | 真实数据集审计 |
| EXP-02-01 | `smoke` | 8/8 类别、来源和证据限制记录 | 不是性能 benchmark，未运行上游系统 |
| EXP-04-01 | `smoke` | 有效 fixture 0 问题，5/5 注入问题类型检出 | 未审计真实数据、媒体、标定和隐私 |
| 第9章 世界模型如何评测与失败 | `reviewed` | 正文、指标排序反转 CPU smoke 与自动驾驶评测矩阵 | benchmark card Schema 与上游运行 |
| 第6章正文 | `reviewed` | prior/posterior、自动驾驶正文、资源边界与 CPU smoke 交叉审查 | PyTorch mini-RSSM 与 GPU 验证 |
| EXP-06-01 | `smoke` | 宿主与 Docker CPU 数据流、3 个单元测试、固定指标 | PyTorch 训练、24GB GPU 资源 |
| 文档站 | `smoke` | 4 章正文接入 MkDocs Material 9.7.7 Docker 严格构建 | 发布部署与浏览器视觉审查 |

状态含义见仓库文件 `specs/PRD/书籍编写与审查执行流程.md`。
