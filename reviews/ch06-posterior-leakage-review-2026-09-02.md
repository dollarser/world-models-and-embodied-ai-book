# 第6章 posterior leakage 与 rollout horizon 审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文不再把“调用 prior”直接等同于 open-loop，而是区分 posterior filtering、从已吸收历史观测的 posterior 起点做一步 prior，以及从共同初态连续展开的 no-reset open-loop。
- **评测合同**：通过。`BENCH-06-01` v3 固定31个转移和 h1/h4/h8/h16/h31；未来观测偏移负对照保持 actions、truth 与初始观测不变，要求 open-loop 精确不变。
- **代码一致性**：通过。`EXP-06-01` v3 输出四类 RMSE、五个 horizon、完整观测可见性审计与既有 KL 诊断；实验卡、benchmark card、中央结果和正文使用同一版本与数值。
- **教学质量**：通过。新增 `TAB-06-03`、`CLAIM-06-07`、练习7与 `SELF-CHECK-06-07`，直接回答“一步 prior 为什么仍可能具有 posterior 历史可见性”。
- **证据边界**：通过。`+1` 偏移明确标为结构探针；单 seed 手写模型不外推为神经 RSSM 的 leakage 频率、跨任务性能、规划价值或 GPU 资源。

## 固定负对照

| 分支 | 原始 RMSE | 后续观测 +1 | 预期 |
| --- | ---: | ---: | --- |
| filtering | 0.060842 | 0.987195 | 改变 |
| posterior-anchored one-step prior | 0.078419 | 0.995413 | 改变 |
| no-reset open-loop | 0.333167 | 0.333167 | 精确不变 |

同一 no-reset rollout 在 h1/h4/h8/h16/h31 的绝对误差约为0.0384/0.0503/0.1719/0.2393/0.6010；只用于确认 horizon 与状态未重置，不声称一般单调性。

## 验证记录

- 第6章单元测试：13项通过；
- 第6章 smoke 与中央 JSON：精确一致；
- 全书门禁：`make smoke-all` 与 `make docs-preview-check` 通过；修正 benchmark metric role 的 Schema 枚举后，`make check`、`check_book.py`、`check_results.py` 与 `git diff --check` 全部通过。站点为29页、22章、23张 Mermaid、134道折叠自检和1161个内部目标；22组 smoke 与中央 JSON 精确一致，68项严格规格测试通过。
