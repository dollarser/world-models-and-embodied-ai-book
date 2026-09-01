# 第5/9/21章 epistemic disagreement 门禁交叉审查

> 日期：2026-09-02
> 范围：第5、9、21章正文，`EXP-05-01` v3、测试、结果、实验卡、PRD 与 manifest
> 结论：补齐“ensemble 可提示未知，也可能共同自信犯错”的可执行负对照；不把手写 range 升级为校准概率、learned OOD 能力或安全证据

## 1. 原问题

第5章已经区分 aleatoric 与 epistemic uncertainty，并建议使用 ensemble/OOD 测试；第9章要求 risk–coverage，第21章消费版本化 score。然而旧 fixture 没有 uncertainty estimator，读者仍可能把“成员一致”误读为“模型知道”。这会使三章的文字边界强于可执行证据。

## 2. 一手资料边界

- Lakshminarayanan et al. 的 Deep Ensembles 把独立初始化网络的预测聚合作为可扩展 predictive uncertainty 基线，并在论文基准上报告校准结果。
- Ovadia et al. 在多种 dataset shift 严重度上比较预测准确率与 uncertainty calibration，显示应在 shift 下而非只在 ID 数据上审计估计器。

来源：

- <https://proceedings.neurips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html>
- <https://proceedings.neurips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html>

这些论文不证明任意 ensemble 都能识别 OOD，也不提供本书手写 range 的校准依据。本书结果不能外推到它们的模型、数据或结论数值。

## 3. 可执行负对照

- score 定义为三个标量成员预测的 `max-min`，固定阈值为 `0.25`。
- ID 例预测 `(-0.1, 0, 0.1)`，target 为 0：range 0.2、ensemble mean 绝对误差 0、不拒绝。
- diverse OOD 例预测 `(1, 2, 3)`，target 为 -2：range 2、ensemble mean 绝对误差 4、触发拒绝。
- shared-error OOD 例预测 `(2, 2, 2)`，target 为 -2：range 0、ensemble mean 绝对误差 4，却不拒绝。
- 输入合同拒绝不足两个成员、非有限预测和布尔阈值。
- 新增 4 个单元测试，第5章由 10 个增至 14 个，全书由 293 个增至 297 个。

## 4. 三章接口闭环

- 第5章把 correlated error 写成 `CLAIM-05-08` 与 `TAB-05-04`，并区分 aleatoric samples、epistemic proxy 和真实错误。
- 第9章要求在冻结 shift 分桶中报告低分歧高损失 false negative，而不只统计高分拒绝率。
- 第21章要求部署 score 绑定成员清单、训练/数据谱系和 estimator revision，并保留独立约束与 fallback 后果。

## 5. 不可外推边界

成员、target、OOD 标签和阈值均为手写标量。range 不是 predictive variance、置信区间、概率、校准误差或正式 OOD score。本实验没有训练独立成员，不估计错误相关性，不运行图像、视频、世界模型、仿真、车辆、机器人或 GPU，也不验证安全门。

## 6. 验证

```text
make ch05-test-local
make ch05-smoke-local
python3 scripts/check_results.py
make check
make ch05-smoke
make smoke-all
make docs-preview-check
git diff --check
```
