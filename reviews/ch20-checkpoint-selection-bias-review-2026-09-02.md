# 第20章 checkpoint selection bias 二次审查（2026-09-02）

## 审查问题

第20章原文已经要求把开发、模型选择和一次性最终集分开，也提醒多 checkpoint、多任务、多指标筛选会产生选择偏差。但该要求只停留在文字层：`EXP-20-01` 没有可执行反例，`BENCH-20-01` 也没有把 checkpoint score 的 split 角色登记为数据合同。因此，读者可能理解原则，却无法用测试发现“看过 final 后再挑 checkpoint”这一常见违规。

## 一手依据与采纳边界

- Cawley & Talbot, *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*（JMLR 2010）：有限样本上的模型选择准则也可能被过拟合，并使后续性能评估产生乐观偏差。来源：<https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf>。
- Dwork et al., *Generalization in Adaptive Data Analysis and Holdout Reuse*（arXiv:1506.02629）：自适应分析反复复用 holdout 会带来泛化问题，并研究了允许受控复用的机制。来源：<https://arxiv.org/abs/1506.02629>。

两项工作只支持“selection 与 evaluation 必须分离、复用 holdout 需要显式治理”的方法论。它们没有产生本书的四行分数，也不支持把 `0.25` 写成普遍或期望 selection bias。

## 已落实优化

1. `EXP-20-01` v8 新增四 checkpoint×三 split 的确定性 score fixture：合法路径只在 selection 上选择；负对照故意最大化 final；confirmation 对两条选择路径均保持 untouched。
2. 合法路径选择 `checkpoint-a`，其 final=`0.50`；错误 final reuse 选择 `checkpoint-d` 并报告 `0.75`，该行 confirmation=`0.50`，因此 authored reuse gap=`0.25`。
3. 实现拒绝空/重复 checkpoint、布尔/非有限/越界分数，以及 selection 或 final 最大值并列；不允许在看到结果后暗选 tie-break。
4. 新增 `CLAIM-20-11`、`TAB-20-05`、`METRIC-20-11`、练习与 `SELF-CHECK-20-07`；实验卡、benchmark card、manifest、capstone trace、PRD、状态和发布说明同步升级。
5. 正文明确：split 的角色由使用方式决定；被用于选择的 final 只能降级为 selection evidence，改名不能恢复独立性。若要确认结论，需要新的、谱系隔离且尚未触碰的数据；无法取得时必须缩小为探索性声明。

## 数值与声明边界

- 四行分数全部由作者构造，不是 checkpoint、策略、仿真器或车辆的运行结果。
- `0.25` 只等于这张表上的 reused-final score 减 untouched-confirmation score，不是期望偏差、置信区间或泛化误差估计。
- confirmation 是教学 oracle；一次 confirmation 也不能排除训练污染、近重复、benchmark API 查询、人工反馈或自适应停止。
- 本阶段没有下载数据/checkpoint，没有 GPU、仿真或真实硬件运行；S 档仍为 Python 标准库、下载 0、GPU 0。

## 验证记录

- 第20章单元测试：26 项通过，其中3项覆盖合法选择、final-reuse 负对照和输入/tie 合同。
- `make smoke-all`：通过，22 章共327项单元测试；第20章 Docker smoke 输出包含精确的 selection/reuse/confirmation 字段。
- `make docs-preview-check`：通过，29个 HTML、22章、23张可访问 Mermaid 图、119道折叠式自检和1161个内部目标。
- `make check-local`：通过，22组 smoke 与中央结果 JSON 精确一致。
- `make check`：通过，4个 Schema、22章、22张实验卡、3张 benchmark card 与67项严格规格测试通过。
- `git diff --check`：通过。

## 后续仍值得优化

真实研究还应保存每次 checkpoint/prompt/阈值查询的时间序列和操作者决策，并研究候选数、反馈轮次、相关候选及排行榜反馈共同作用下的 adaptive overfitting。当前确定性反例只把角色错误变得可见，不替代嵌套评测、受控 reusable holdout 或真正私有的一次性最终集。
