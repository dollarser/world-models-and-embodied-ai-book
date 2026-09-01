# 第9章概率评分与校准二次审查（2026-09-02）

## 审查结论

第9章已经覆盖动作干预、长时缺失、策略排序、OOD risk–coverage 与闭环效用，但“校准”主要作为应报告字段出现。原 `EXP-09-01` 没有概率预测，读者无法从可执行反例看出：ECE 依赖分箱，粗分箱可把无信息 base-rate forecast 记为零误差，而 calibration error 本身不等于完整 probabilistic forecast quality。

## 一手依据与边界

- Gneiting & Raftery, *Strictly Proper Scoring Rules, Prediction, and Estimation*：proper scoring rule 在期望意义上鼓励诚实报告预测分布，并区分 calibration 与 sharpness。来源：<https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf>。
- Guo et al., *On Calibration of Modern Neural Networks*：使用 reliability diagram、固定分箱 ECE 等方法研究神经网络校准。来源：<https://proceedings.mlr.press/v70/guo17a.html>。

这些来源支持并列 proper score、校准诊断和分箱协议；它们不为本书四行手工数值背书，也不意味着 ECE、Brier 或 log loss 中任一个可以单独证明部署概率可靠。

## 已落实优化

1. `EXP-09-01` v3 新增四个固定二元结果 `1,1,0,0`，比较 uniform `0.5` 与 informative `0.9,0.9,0.1,0.1` 两组概率。
2. 两行在单个 `[0,1]` bin 下 ECE 都为0；Brier 为 `0.25/0.01`，log loss 为 `0.693147/0.105361`。informative 行在 `[0,0.5), [0.5,1]` 两个固定 bin 下 ECE 为0.1。
3. 代码显式登记 bin edge、最后一 bin 闭区间、空 bin 跳过和概率严格位于 `(0,1)` 的 log-loss 合同；拒绝非 Boolean outcome、长度不一致、非有限/边界概率与未覆盖 `[0,1]` 的 bin。
4. `BENCH-09-01` v3 新增 Brier、log loss 与 fixed-bin ECE 三项指标，保持 `distribution_shift.enabled=false`：这张概率表不是 learned uncertainty estimator、calibration split 或 OOD 总体。
5. 正文新增 `CLAIM-09-09`、`TAB-09-03`、概率评分练习与自检，并同步实验卡、结果、manifest、PRD、状态和发布说明。

## 不允许的外推

- 四例上的 ECE=0 不证明总体 calibration；两 bin ECE=0.1 也不证明 uniform forecast 更好。
- 预测方差只是这张表上概率离开均值的离散度，不是 epistemic uncertainty、sharpness 的完整估计或安全指标。
- proper score 的有限样本排序不是“真实概率已恢复”的证明；仍需独立样本、场景/horizon 分层、区间与决策后果。
- 本阶段没有下载数据、checkpoint 或模型，没有运行 GPU、仿真器、机器人或车辆。

## 验证记录

- 第9章12项单元测试通过，覆盖数值、分箱敏感性和非法输入。
- `make smoke-all` 通过：22章共330项单元测试。
- `make docs-preview-check` 通过：29个 HTML、22章、23张可访问 Mermaid 图、120道折叠式自检和1161个内部目标。
- `make check-local` 通过：22组 smoke 与中央结果 JSON 精确一致。
- `make check` 通过：4个 Schema、22章、22张实验卡、3张 benchmark card 与67项严格规格测试通过。
- `git diff --check` 通过。

## 后续缺口

真实小型 M 档应在许可数据上预注册 event definition、calibration/final split、horizon 与场景分桶，比较 reliability diagram、Brier/log loss、校准前后阈值决策以及 fallback 后果。当前 S 档只建立指标合同，不替代 learned model calibration experiment。
