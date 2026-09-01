# 第21章严重度分层选择性风险审查

> 日期：2026-09-02
> 范围：第21章正文、`EXP-21-01` v7、测试、结果、实验卡、manifest、PRD 与第22章 trace

## 问题与证据

旧 fixture 已报告 coverage、接受失败率和拒绝捕获的失败比例，但每个 failure 都按一个事件计数。两个 gate 即使留下完全不同严重度的失败，也可能得到相同汇总数。

- [NHTSA Automated Lane Centering 功能安全评估](https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/13498a_812_573_alcsystemreport.pdf)按 severity、exposure、controllability 评估车辆级 hazard，支持把严重度从事件计数中拆开；它不为本书权重定标。
- Tolksdorf et al. 2026 年预印本 [Risk Estimation for Automated Driving](https://arxiv.org/abs/2601.15018)把状态估计不确定性与潜在碰撞严重度作为风险估计的不同组成部分；本书没有复现论文方法、代码或实验。

## 实现与边界

`severity_stratified_selective_audit()` 固定四个成功、一个 authored weight 1 的失败和一个 authored weight 10 的失败。两个负对照都接受4/6、留下1/4失败，并按个数拒绝1/2失败；只交换被接受的失败身份。结果分别为：

| 对照 | 接受失败权重 | 按权重拒绝召回 |
| --- | ---: | ---: |
| 拒绝高权重失败 | 1 | 0.909091 |
| 拒绝低权重失败 | 10 | 0.090909 |

输入合同拒绝重复/空 case ID、非布尔失败标签、布尔/非有限/非正权重、空/重复/未知接受 ID。三个新增测试分别覆盖数值不变量、非法输入和 `evaluate()` 接线。

`1/10` 被明确标为作者设置的无外部标定的敏感性分析代理权重：它不是事故概率、AIS 等级、伤亡、货币成本或经验证的真实风险。正文要求在权重缺少外部依据、严重度标签不可靠、暴露分母不足或 fallback 后果未经闭环验证时停止道路部署外推，保留 failure type、case ID、场景/道路使用者/速度分桶和来源，而不是发布一个伪精确总分。

## 一致性结果

- `EXP-21-01` 升级为 fixture v7，并由 `CLAIM-21-14`、`TAB-21-06` 和实验卡反向绑定；
- 第22章 deployment/safety trace 同步到 `fixture-v7`，仍只验证 metadata 图；
- 全书当前为187条声明、95条 `result`、321个章节测试；
- 未下载数据/checkpoint，未运行模型、GPU、仿真器、机器人或车辆。

## 验证结果

- `make smoke-all`：通过，22章共321个章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、117个折叠式自检和1161个内部目标；
- `make check`：通过，4个 Schema、67个严格规格测试与22组结果精确比对均通过；
- `git diff --check`：通过。
