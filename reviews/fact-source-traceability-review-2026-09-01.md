# 全书事实声明来源追溯审查

> 日期：2026-09-01
>
> 范围：164 条关键声明中的全部 `fact`、一手论文/官方资产、本书定义与当前仓库合同
>
> 结论：通过；事实登记完整性形成自动门禁，来源蕴含仍保留人工审查责任

## 1. 为什么需要独立事实登记

原有合同能保证声明 ID、类型、章节归属与 `result` 实验绑定正确，却无法回答一条 `fact` 应去哪里核对。审计发现事实依据至少分为六类：同行评审/预印本、官方代码或文档、供应商页面、本书工作定义、当前仓库合同，以及正文内可复核的数学恒等式。若只保存正文链接，后续无法自动发现事实改型后留下的陈旧来源，也容易把供应商定位误当成独立验证。

## 2. 类型修正

三条原 `fact` 实际表达作者的最低完成定义或评测建议，已改为 `recommendation`：

- `CLAIM-11-01`：动作反事实需要同状态动作干预与方向检查；
- `CLAIM-18-01`：VLA 后训练实验至少应登记哪些组成；
- `CLAIM-21-01`：部署延迟报告至少应包含哪些测量字段。

当前 164 条声明分布为：26 条 `fact`、75 条 `result`、9 条 `inference`、54 条 `recommendation`。本轮没有改变任何实验输出或把未验证结论升级为结果。

## 3. 一手来源抽查

- [PlaNet ICML 论文](https://proceedings.mlr.press/v97/hafner19a.html)支持确定性/随机潜在转移与潜在空间规划接口；
- [Dreamer ICLR 论文](https://openreview.net/forum?id=S1lOTC4tDS)支持从经验数据学习 latent dynamics、再在 imagination 中学习 value/action 的双循环；
- [V-JEPA 2.1 预印本](https://arxiv.org/abs/2603.14482)与[官方仓库](https://github.com/facebookresearch/vjepa2)支持 dense predictive loss、deep self-supervision 和公开模型入口；
- [Cosmos-Predict2.5 官方仓库](https://github.com/nvidia-cosmos/cosmos-predict2.5)明确声明转为有限维护并指向 Cosmos 3；
- [LeRobot ACT 实现](https://github.com/huggingface/lerobot/blob/main/src/lerobot/policies/act/modeling_act.py)区分逐步 temporal ensemble 与动作队列路径；
- [NIST V&V 指南](https://www.nist.gov/publications/summary-industrial-verification-validation-and-uncertainty-quantification-procedures)区分实现/求解核验与预期用途下的现实有效性；
- [GAIA-4 官方页面](https://wayve.ai/thinking/gaia-4/)只登记为 `vendor_statement` / `V`，不支持独立保真、安全或相关性结论。

## 4. 机器合同

新增 `specs/fact-evidence.json`，每条事实登记：

- `basis`：`primary_source`、`official_asset`、`vendor_statement`、`book_definition`、`repository_contract` 或 `mathematical_identity`；
- `maturity`：沿用 `P/A/O/V/T`，内部合同使用 `internal`；
- `anchors`：外部一手来源或仓库内可核对文件；
- `scope_note`：来源支持到哪里、不能推出什么；
- 顶层 `audit_date`：本轮共同核查日期。

门禁拒绝漏登记、多余/已改型登记、重复 ID、非法证据基类/成熟度、缺失锚点、本地锚点不存在和没有边界说明。论文/官方/供应商依据必须含外部锚点，本书定义/仓库合同/数学恒等式必须含本地锚点。

## 5. 验证与限制

- 新增 4 个正反向规格测试；规格测试总数由 33 增至 37；
- 完整 `make check`、`make docs-preview-check`、结果一致性与 Git 差异检查在提交前复跑；
- 自动门禁证明“有登记且结构合理”，不证明某个来源在语义上蕴含整句事实；
- GitHub `main`、官方文档和供应商页面会变化，涉及当前版本的条目仍需按研究雷达周期复核；
- 本轮不下载 checkpoint 或数据，不运行 GPU、仿真、机器人或车辆实验。
