# 第12章 occupancy 类别不平衡与评测 mask 审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文把 overall accuracy、occupied recall/IoU、observed evaluation mask 与规划 unknown 语义拆成四个字段，不再让单一高 accuracy 支持可行动空间声明。
- **实验合同**：通过。`EXP-12-01` v5 冻结49格全域和13格 observed-only 两个分母；两个多数类 predictor 都漏掉全部3格 occupied。
- **代码一致性**：通过。全域 all-unknown 为36/49=`0.734694`，observed-only all-free 为10/13=`0.769231`；两者 occupied recall/IoU 均为0，后者显式记录 omitted=36。
- **教学质量**：通过。新增 `TAB-12-07`、`CLAIM-12-12`、练习8与 `SELF-CHECK-12-08`，直接解释“不计分”不能改写成“可通行”。
- **证据边界**：通过。类别比例、predictor 和 mask 都是手写诊断，不是 occupancy 模型、真实数据集、碰撞风险或规划安全性能。

## 分母对照

| 计分域 | predictor | correct/total | occupied recall/IoU | omitted |
| --- | --- | ---: | ---: | ---: |
| 全域 | all-unknown | 36/49 | 0/0 | 0 |
| observed-only | all-free | 10/13 | 0/0 | 36 unknown |

Observed mask 可以是 benchmark 的合法计分策略，但规划器仍需保留被排除格子的 unknown 状态，除非另有清空证据。

## 验证范围

- 第12章单元测试：23项；
- smoke 与中央结果：要求精确一致；
- 全书目标计数：207条声明、115条结果、387个章节测试、137道练习；
- 完整门禁在提交前运行；没有真实 RGB-D/点云、学习模型、仿真、GPU、机器人或车辆。
