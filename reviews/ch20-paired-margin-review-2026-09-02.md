# 第20章 paired margins 与 joint outcome 审查

> 日期：2026-09-02
> 范围：`CLAIM-20-12`、`TAB-20-06`、`EXP-20-01` / `BENCH-20-01` v9
> 结论：边际成功率不能替代配对联合表；新增 exact conditional 诊断不改变 cluster、效应区间和真实策略评测的未验证状态

## 1. 发现的问题

第20章已保存十对 candidate/baseline 身份，并正确区分 episode-micro、route-macro 与 cluster bootstrap；因此“完全忽略配对”不是当前缺陷。但正文尚未给出一个只改变 joint pairing、同时严格固定两边边际成功率的负对照。读者可能仍把 `candidate=60%`、`baseline=40%`、差值 `+20pp` 当成足够完整的 paired evidence。

## 2. 一手方法证据

- Fay et al., [Confidence Intervals for Difference in Proportions for Matched Pairs Compatible with Exact McNemar's or Sign Tests](https://pmc.ncbi.nlm.nih.gov/articles/PMC9447366/)：matched binary conditional test 以 discordant pairs 的方向做 exact binomial 计算，并区分检验与效应区间。

本书实现明确冻结 equal-tail exact conditional two-sided 版本。没有把 `p` 值写成效应量，也没有声称 exact test 自动处理 route cluster、multiplicity、adaptive analysis 或 equivalence。

## 3. 负对照设计

两张表都固定20对：

| 表 | both success | candidate only | baseline only | both failure | candidate/base | 差值 | discordant | exact two-sided |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high-concordance | 8 | 4 | 0 | 8 | 0.6/0.4 | +0.2 | 4 | 0.125 |
| more-discordant | 4 | 8 | 4 | 4 | 0.6/0.4 | +0.2 | 12 | 0.387695 |

两表边际数完全相同，只有 joint cells 不同。该构造证明两列成功率和点差不能恢复 discordant count 或具名条件诊断。它不证明 discordant 越多时证据必然更弱；数值由方向比例与总 discordant 数共同决定。

## 4. 代码与声明边界

- `exact_mcnemar_report()` 验证非空序列、唯一 `pair_id` 和严格 Boolean outcome；零 discordant 时返回 `p=1`。
- `paired_margin_diagnostic()` 固定两张20对表，并验证边际成功率相等。
- `smoke.py` 锁定 `0.125` 与 `0.387695`，中央结果 JSON 精确保存 joint counts、零假设和 scope。
- `CLAIM-20-12` 禁止外推策略效应、显著性功效、cluster 相关、等效性、多重比较和部署安全。
- route/scene/seed family 嵌套时仍须在 cluster 层分析；episode-level McNemar 不会修复伪重复。

## 5. 验证

- `make ch20-test-local`：通过，29项；
- `make smoke-all`：通过，全书333项章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、121个折叠自检和1161个内部目标；
- `make check`：通过，4个 Schema、22章、22张实验卡、3张 benchmark card 与67项严格规格测试；
- `git diff --check`：通过。

## 6. 保留限制

两张表均为 MIT 手工 fixture，不是仿真、机器人、车辆或任何模型结果。当前没有实现 matched-pair effect interval，也没有真实独立 pair、cluster、预注册、多重比较或外部效度证据。GPU、数据下载和硬件状态不变。
