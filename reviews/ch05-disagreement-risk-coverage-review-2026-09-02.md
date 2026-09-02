# 第5章 disagreement 排序与 risk–coverage 审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文区分成员 range、ensemble mean error、coverage、接受 failure rate、failure recall 与正确样本 defer。
- **代码一致性**：通过。`EXP-05-01` v4 的四例 panel 同时包含低 range 共同错误和高 range 正确预测；阈值0/0.25/2的 coverage 为0.25/0.5/1，risk 为1/0.5/0.5。
- **输入合同**：通过。计算器拒绝空 case、重复 ID、无效成员集合、非有限/负阈值和含糊 error tolerance。
- **证据强度**：通过。所有预测、target、OOD/failure 标签、容差和阈值均为作者设定，未写成总体风险、校准或安全收益。

## 停止边界

该反例只能证明 range 排序可能与真实错误排序不一致。生产 gate 仍需独立冻结 split、估计不确定性、区间与分桶，并验证 fallback 后果；四个点不能用于阈值选择。
