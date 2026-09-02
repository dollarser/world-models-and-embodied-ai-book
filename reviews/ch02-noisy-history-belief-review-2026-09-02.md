# 第2章噪声历史与 belief 边界审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文把 current observation、noisy history belief 和 perfect-history oracle 分成三层，不把 history presence 当成 state sufficiency。
- **代码一致性**：通过。`EXP-02-01` v4 按等权 prior 与对称 `0.8/0.2` cue likelihood 计算 posterior、Bayes action、0.38 mean return 与0.22 oracle regret。
- **输入合同**：通过。校验器拒绝 context ID 不匹配、非概率 prior、likelihood 缺项/越界/未按 context 归一化及 cue 下 Bayes action tie。
- **证据强度**：通过。prior、likelihood 与一步 return 均为作者设定；没有训练 filter、sequence model 或 POMDP policy。

## 停止边界

0.28 history gain 只属于固定两 context、两 cue、两 action 的已知概率表。它不证明 likelihood 校准、belief 可学习、长时更新正确、memory 泛化或真实系统性能。
