# 第17章代理评测组件归因审查

> 审查日期：2026-09-02
> 范围：第17章、`EXP-17-01` v4、`CLAIM-17-10`、`TAB-17-03`
> 结论：通过；正文、组件 trace、实验卡与登记结果一致

## 原有缺口

正文已经区分动作注入、world-model rollout 和 outcome scorer，但没有把 state/pose decoder 单列，也没有可执行证据证明最终分数不能定位故障来源。只报告策略相关性或成功率时，action schema、transition、pose/event extraction 与 judge 的错误会被折叠为一个数字。

## 一手资料复核

- [KineBench](https://arxiv.org/abs/2607.19876)明确把 IDM action extraction 视为 world-model 物理评测的归因混杂，并以 segmentation、metric depth、6D pose tracking 的显式管线降低混淆；论文同时保留这些模块自身的可靠性边界。
- [WorldArena 2.0](https://arxiv.org/abs/2605.17912)把世界模型评测扩展到视触觉、交互式策略优化、仿真与真实机器人平台，说明组件账必须按模态、用途与平台重新验证。

两项工作支持“分段记录和校准”，不证明任何 decoder、scorer 或 learned simulator 已由本书复现。

## 修改与固定证据

- 新增 action grounding、transition model、state decoder、outcome scorer 四段 trace；
- oracle 场景选择 `safe_route`，Spearman `1.0`，真实 regret `0`；
- action-grounding 单故障选择 `idle`，真实 regret `1.05`；
- transition、decoder、scorer 三个不同单故障得到相同代理分数 `{phantom_shortcut: 1.0, safe_route: 0.85, idle: -0.2}`，均选择真实碰撞的 shortcut，Spearman `-0.5`，真实 regret `1.85`；
- 中间 trace 分别在 predicted terminal、decoded terminal 和 final score 首次分歧，因此能够定位故障段。

## 证据边界

五个场景是确定性单故障 fixture，不估计现实故障率、相关性、交互项或 additive error budget；terminal label 不能替代真实 6D pose、depth、segmentation、VLM judge 或安全事件检测。没有运行模型、仿真器、机器人、车辆、数据下载或 GPU。

## 门禁结果

- `make smoke-all`：通过，22章共315个章节测试，22组 smoke 与登记结果精确一致；
- `make docs-preview-check`：通过，29个 HTML、22章、23个可访问 Mermaid 图、116个折叠自检、1161个站内目标；
- `make check`：通过，4个 schema、22章、22张实验卡、3张 benchmark card 与67个严格规格测试；
- `git diff --check`：通过。
