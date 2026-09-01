# 第20章相关 episode、配对比较与 cluster bootstrap 审查

> 日期：2026-09-01
> 范围：第20章、`EXP-20-01` v5、`BENCH-20-01` v5
> 结论：把“相关 episode 不能直接套独立二项区间”的文字限制落实为配对 route fixture、结果、实验卡、benchmark card 与测试

## 1. 原有缺口

第20章已经说明同一任务、场景或路线的重复运行会相关，并建议 cluster bootstrap；但 v4 代码只实现 Wilson interval。读者能看到限制，却不能运行一个会因 cluster 权重而改变结论的反例，也无法检查配对身份是否在重采样中保留。

## 2. v5 设计

新增 10 对 candidate/baseline 二元结果，嵌套在 4 条 route：`route-a/b` 各 4 对，`route-c/d` 各 1 对。每一对先计算 `candidate-baseline`，再分别形成：

- episode-micro estimand：10 对等权；
- route-macro estimand：先求 route 内均值，再让 4 条 route 等权；
- route-level bootstrap：一次 replicate 有放回抽 4 条 route，保留 route 内的配对差。

四个 route 只有 `4^4=256` 种有序重采样，代码全部枚举，避免 Monte Carlo seed 与有限重复误差。简单线性 percentile 端点仍只是一种教学选择，不声称优于 BCa、bootstrap-t、wild cluster bootstrap 或模型化分析。

## 3. 固定结果与解释

| 输出 | v5 结果 | 允许解释 | 禁止解释 |
| --- | ---: | --- | --- |
| candidate/baseline micro 成功率 | 0.9 / 0.6 | episode 暴露量等权时差为 +0.3 | 候选策略普遍更好 |
| episode-micro 配对差 | +0.3 | 重复较多的 route-b 权重更大 | 独立样本量为 10 |
| equal-route macro 配对差 | 0.0 | 四条预注册 route 等权时点差为 0 | 两策略等效 |
| 256 replicate percentile 95% | [-0.75, 0.75] | 四 cluster 下机制和离散性可见 | 可靠 95% population coverage |

区间包含零不证明等效；等效性需要预先定义 margin、合适设计与相应检验。micro 与 macro 也没有普遍赢家：若部署总体按真实 episode 暴露量定义，micro 可合理；若 route 是同权独立单元，macro 更贴近问题。权重和独立单元必须在看结果前冻结。

## 4. 来源边界

[Field & Welsh (2007)](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x)讨论 clustered data 的不同 bootstrap、模型假设与一致性条件。本书只据此支持“cluster 模型和重采样设计必须显式”的方法边界；v5 数字全部来自本书手工 fixture，不是该论文结果复现。

## 5. 代码和资产一致性

- `exact_paired_cluster_bootstrap()` 验证非空、唯一 pair、cluster 数、布尔 outcome、confidence 与枚举预算；
- candidate/baseline 始终在 pair 内作差，route 重采样不拆散配对；
- `EXP-20-01`、`BENCH-20-01`、结果 JSON、manifest、正文 `CLAIM-20-08` 与 `TAB-20-02` 已同步为 v5；
- 新增 3 个测试，覆盖 micro/macro estimand、256 个精确 replicate 与非法采样合同。

## 6. 保留限制

- 四条 route 远少于可靠渐近推断通常需要的独立 cluster 数；
- route 和 outcome 都是手工构造，不代表真实机器人、自动驾驶或 benchmark 分布；
- 没有处理多层 cluster、时间自相关、缺失配对、分层抽样、连续 outcome 或多重比较；
- 当前无 GPU 且无需 GPU，本轮没有下载数据、安装仿真器或运行任何策略。

## 7. 门禁

阶段提交前的实测结果如下：

- 第20章 17 个单元测试与 CPU smoke 通过，固定输出和注册结果 JSON 精确一致；
- `make check` 通过：22 张实验卡、22 份 smoke 结果、4 个 Schema、22 章、3 张 benchmark card 与 49 个严格规范测试均通过；
- `make docs-preview-check` 通过：28 个 HTML 页面、22 个编译章节、23 个可访问 Mermaid 图和 1073 个内部目标均有效；
- `git diff --check` 作为提交前最后一项空白符门禁执行。
