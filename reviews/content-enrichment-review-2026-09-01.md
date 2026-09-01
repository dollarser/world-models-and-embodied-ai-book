# 内容增强审查：评测统计、动作分块、最新研究与读者术语表

> 日期：2026-09-01
> 范围：第9、13、20章，`EXP-20-01`，在线导航与术语索引
> 目标：提高内容准确性、教学密度、证据边界和正文—代码—结果一致性

## 审查结论

本轮没有通过堆叠模型名称扩大篇幅，而是修复三处高价值缺口：第20章把“小样本应报告区间”落成公式、代码、测试和结果；第13章把 action chunk 从模型概念扩展为可执行接口合同，并明确其无法消除分布偏移；第9章加入 2026 年闭环世界模型评测案例，同时维持 `R0–R1` 与“本书未运行”的边界。另新增读者术语表，避免作者侧规格成为唯一查词入口。

## 来源复核

| 内容 | 使用的一手来源 | 写入边界 |
| --- | --- | --- |
| ACT 执行动作数与动作块 | LeRobot 官方 `modeling_act.py` | 只描述当前官方实现的 queue、chunk 与 `n_action_steps`，不声称本书训练过 ACT |
| WorldArena 2.0 | arXiv:2605.17912 与官方项目页 | 只作为 modality/functionality/platform 评测设计案例，不抄排行榜 |
| KineBench | arXiv:2607.19876 | 只讨论 IDM 带来的归因混淆与论文提出的 kinematic grounding，本书未运行 |
| Wilson interval | NIST Engineering Statistics Handbook | 使用标准 Wilson 公式，并显式保留独立 Bernoulli 假设与相关样本限制 |

## 代码与结果一致性

`EXP-20-01` 新增 `wilson_interval(successes, trials)`，覆盖点估计包含性、`4/4` 不代表确定性、非法计数与布尔输入。固定结果为：

- easy goal-only：`4/4`，点估计 `1.0`，Wilson 95% 区间 `[0.510109, 1.0]`；
- full safety-aware：`5/8`，点估计 `0.625`，Wilson 95% 区间 `[0.305742, 0.863156]`。

区间不能消除两协议在任务总体、成功定义和分母上的三项差异。实验卡数据版本升为 `v2`，声明、指标、限制和结果 JSON 已同步。

## 已执行门禁

```text
make ch20-test-local       # 7 tests
make ch20-smoke-local      # 固定结果与断言通过
make check-local           # manifest、22 张实验卡、22 组结果精确一致
make docs-build            # MkDocs strict 通过
make docs-preview-check    # 27 HTML、22 章、977 个内部目标
make smoke-all             # 22 章 Docker CPU smoke，139 tests
git diff --check           # 通过
```

完整 Docker smoke 已在本轮阶段提交前再次执行；它仍只运行 CPU fixture，不下载大数据、不需要 GPU 或硬件。

## 保留限制与下一轮优先级

- WorldArena 2.0、KineBench 与 LeRobot 均未在本机运行；版本漂移后需按资料核查日期重审。
- Wilson 区间不适用于无修正的相关 episode；后续可增加按任务/场景 cluster bootstrap 的标准库或小型 NumPy 教学 fixture。
- 在线术语表覆盖核心路径，但尚未建立自动术语反向索引和中文/英文别名搜索测试。
- 第5章、第13章和第20章仍是篇幅相对短、值得继续深化的章节；下一轮应优先补“错误诊断树”和跨章案例，而不是扩充排行榜。
