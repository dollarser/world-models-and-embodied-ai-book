# 第20章零事件 pseudo-replication 审查

> 日期：2026-09-02
> 范围：第20章正文、`EXP-20-01`/`BENCH-20-01` v7、测试、结果、实验卡、PRD 与第22章 trace

## 审查问题

旧版已经明确 `0/100→2.9513%` 的精确一侧二项上界依赖100次独立 Bernoulli 暴露，但“相关 route 不适用”只停留在限制文字。读者仍可能把同一路线、初态族或生成谱系的重复 replay 全部塞进 `n`，得到看似更窄的数值。

[Hanley 与 Lippman-Hand](https://pubmed.ncbi.nlm.nih.gov/6827763/)支持零分子上界的基本计算；[Field 与 Welsh](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x)说明 clustered-data bootstrap 必须匹配 cluster 模型和重采样设计。当前 [Waymo Safety Impact](https://waymo.com/safety/impact/) 还按城市与地理暴露匹配道路 benchmark，并明确真实 AV/人类数据不存在完美 apples-to-apples 对照。后者是供应商的一手方法说明，不为本书 fixture 或道路安全性背书。

## 新增合同

固定10条 authored route，每条10次 replay，全部零事件：

| 独立单位 | 目标量 | `n` | 95%一侧上界 |
| --- | --- | ---: | ---: |
| episode | 独立抽取 episode 的事件概率 | 100 | 0.029513 |
| route cluster | 新 route 在其重复测量中至少出现一次事件的概率 | 10 | 0.258866 |

两行不是同一参数，第二行不是第一行的“相关性修正”。把每条 route 的重复数从1增加到10时，独立 cluster 数仍为10，因此公式数值仍是0.258866；但 cluster outcome 已从“一次内至少一例”变成“十次内至少一例”，不能解释为同一风险不变。假设所有 episode 独立的 per-episode 上界则机械收窄。

代码拒绝非整数、布尔、零或负 cluster/repeat 数，并复用既有 confidence 合同。三个新增测试分别验证固定数值、只增加重复不会创造 cluster，以及非法输入。

## 边界与停止条件

- fixture 不估计 intracluster correlation、design effect 或有效样本量；
- 不能用 `0.258866/0.029513` 宣称真实风险相差某个倍数；
- 不能把10条 route 当作未经模型证明的 per-episode 有效样本量；
- 缺少 route/scene/seed/生成谱系或重复结构时，停止发布总体上界，只报告零事件计数与已知暴露结构；
- 真实 per-episode 推断需要预注册相关数据模型和足够 cluster，真实新场景失败发现需要增加独立场景覆盖。

## 一致性结果

- 新增 `CLAIM-20-10`、`TAB-20-04`、`METRIC-20-10` 和一组练习/自检；
- `EXP-20-01`、`BENCH-20-01` 与第22章 independent-evaluation trace 同步到 v7；
- 全书登记口径更新为188条声明、96条 `result`、324个章节测试与118道练习；
- 没有下载、模型、GPU、仿真器、机器人或车辆运行。

## 验证结果

- `make smoke-all`：通过，22章共324个章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、118个折叠式自检和1161个内部目标；
- `make check`：通过，4个 Schema、67个严格规格测试与22组结果精确比对均通过；
- `git diff --check`：通过。
