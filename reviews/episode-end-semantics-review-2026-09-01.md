# 第4/8/20章结束语义与评测分母交叉审查

> 审查日期：2026-09-01
> 范围：第4、8、20章正文，`EXP-04-01` v3，`EXP-08-01` v2，`EXP-20-01`/`BENCH-20-01` v3，fixture、测试、结果与 manifest
> 结论：第4章的数据结束标志已贯通 imagined value target 和评测 episode accounting；GPU、仿真与真实故障率状态不变

## 1. 发现的问题

第4章已经区分 `terminated` 与 `truncated`，但第8章旧 fixture 直接接收手工 discount，无法证明 timeout 的 value bootstrap 构造正确。第20章旧聚合器直接使用 `len(selected)`，正文要求的 timeout、截断和有效分母没有机器可读证据。两处都属于正文强于实现的跨章接口缺口。

## 2. 修复与可执行反例

- 第8章新增 `bootstrap_discounts`：两类结束都会关闭采样窗口，只有 `terminated` 关闭 value bootstrap；需要 bootstrap 时若下一观测无效则拒绝 target。
- 依据 Gymnasium 当前 `TimeLimit` 官方实现，撤销“两个结束标志必须互斥”的过强假设；双真合法且由 `terminated` 主导 bootstrap。第4章原冲突注入改为真正的非布尔结束标志，仍保留 8 类错误覆盖。
- 单步反例固定 `reward=1`、`next_value=4`：自然终止 target 为 1，有效截断 target 为 5，折叠 `done` 后错误损失 4。
- 第20章每行增加 `terminated/truncated`、`valid` 与 `invalid_reason`。至少一个结束标志为真；两者允许同一步双真，并分别计入结束原因但只贡献一个 attempted episode。完整协议显式报告 `8 attempted / 8 valid / 7 terminated / 1 truncated / 0 invalid`，有效 timeout 作为失败保留在 `5/8` 分母。
- 注入 `reset_failed` 的技术无效运行时，审计器保留 ID/原因并阻止聚合；未来若允许重跑、替换或排除，必须在运行前冻结政策。

## 3. 声明边界

这些测试只证明手工合同和拒绝路径一致，不估计 Dreamer continuation head、真实 benchmark timeout 分布、reset/logging 故障率或策略性能。Wilson 区间仍只在固定协议与独立 Bernoulli 假设下解释；无效运行政策不能由观察结果后决定。

## 4. 验收

- 第4章由 13 增至 14 个单元测试，第8章由 7 增至 12 个，第20章由 7 增至 12 个，全书由 152 增至 163 个；
- 两章 smoke 与结构化结果精确一致；
- 4 个 Schema、18 个 Schema 契约测试、22 张实验卡、3 张 benchmark card、22 组结果、严格文档构建和本地预览检查均纳入阶段门禁。
