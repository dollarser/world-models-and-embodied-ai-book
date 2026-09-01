# 第17章 prospective policy ranking 审查

> 审查日期：2026-09-02
> 范围：第17章、`EXP-17-01` v5、`CLAIM-17-11`、`TAB-17-04`
> 结论：通过；策略分区、正文结论、实验卡与登记结果一致

## 原有缺口

正文要求对新增策略重新校准，却没有在代码中区分用于选择 world model/scorer/阈值的策略与模型冻结后首次进入的策略。若同一批 checkpoint 同时参与调参与报告，相关性只能说明 retrospective fit，不能证明下一次策略更新仍保持排序。

## 一手资料复核

[Interactive World Simulator](https://arxiv.org/abs/2603.08546)报告比较 DP、ACT、`π0`、`π0.5` 的 final/intermediate checkpoints，在四项任务、每项20个来自 simulator 训练分布的初态上配对 world-simulator 与真实机器人分数，并报告相关性和区间。这是作者协议内的配对证据，不自动覆盖新的 policy family、训练 lineage、动作 schema 或 OOD 初态；本书没有运行模型或复核论文数值。

## 修改与固定证据

- calibration panel 只含 `safe_route/idle`，模型 return 与真实规则完全相同，Spearman `1.0`、最大绝对 gap `0`；
- 模型和评分规则冻结后加入不相交 `phantom_shortcut`；其模型—真实 return gap 为 `2.0`；
- 三策略 prospective Spearman 变为 `-0.5`，代理选中真实 collision 策略，regret `1.85`；
- 输入合同拒绝空 panel、重复策略、未知策略、跨 panel 重叠和非 tuple held-out panel。

## 证据边界

两策略 Spearman 只是脆弱的顺序检查；一个手工 held-out policy 不估计 learned policy family、checkpoint lineage、任务或初态 shift 下的泛化概率。fixture 不包含策略训练、模型选择过程、真实 evaluator 噪声或重复种子。

## 门禁结果

- `make smoke-all`：通过，22章共318个章节测试，22组 smoke 与登记结果精确一致；
- `make docs-preview-check`：通过，29个 HTML、22章、23个可访问 Mermaid 图、116个折叠自检、1161个站内目标；
- `make check`：通过，4个 schema、22章、22张实验卡、3张 benchmark card 与67个严格规格测试；
- `git diff --check`：通过。
