# 第7章重规划预算与回报口径审查

> 审查日期：2026-09-01
> 范围：第7章正文、`EXP-07-01` v3、实验卡、fixture、测试与中央结果

## 1. 发现的问题

原固定扰动表把执行旧 suffix 的 2 个扰动后动作，与重新规划的 3 个扰动后动作比较。`-0.2` 对 `0.7` 虽是代码真实输出，却同时改变反馈方式和执行预算，不能把差值归因于 replanning。正文曾提示“执行步数不同”，但仍把两行放在主要结果表，容易让读者误读为受控比较。

另一个边界是 terminal value：它进入有限时域规划目标，并不等于 deadline 前已经观测到的环境 reward。若结果只提供一个 `return`，读者无法判断收益来自真实 transition reward，还是来自 bootstrap。

## 2. 修正后的协议

旧版不等预算输出被保留为 `legacy_unequal_budget` negative control，并明确标记 `post_disturbance_action_budget_equal=false`。新增两个共享 2 个扰动后动作槽的协议；字段只表示动作预算是否可比，不把单个手工 fixture 标为普遍“因果有效”：

- `fixed_budget_reward_only`：stale suffix 的环境回报为 -0.2；replanning 立即 harvest，环境回报为 -0.1；
- `fixed_budget_with_terminal_value`：stale suffix objective 为 -0.2；replanning 执行两次 advance，环境回报 -0.3，terminal-value contribution 1.0，objective 0.7。

第二组没有声称环境已经获得 0.7，也没有声称完成 harvest。它只验证冻结 terminal value 怎样改变有限时域动作排序。所有数值包含扰动前已执行动作的 -0.1 reward。

## 3. 代码与输入合同

`rollout` 现在同时返回 `environment_return`、`terminal_value_contribution` 和二者之和 `return`。扰动执行器显式返回规划动作、实际执行动作与可用动作预算，并拒绝非布尔 `replan`、非正预算、超过 stale suffix 的固定预算，以及没有固定 deadline 却注入 terminal value 的歧义调用。

新增 3 个测试覆盖：旧协议预算不等的暴露、固定预算 reward-only 对照、terminal value 分账与无效协议输入。第7章由 10 个增至 13 个测试，全书由 279 个增至 282 个。

## 4. 来源与教学边界

正文用 MIT *Underactuated Robotics* 的 MPC 循环核对“测量—优化—执行首步—重复”的定义，并将 PlaNet 链接改为 PMLR 正式论文页。来源用于算法接口，不为本书 fixture 的数值背书。

本次仍只运行标准库解析 fixture：没有 learned dynamics/value、随机扰动分布、CEM/MCTS、仿真、GPU、机器人或车辆。一个固定 deadline 下的 0.1 改善不代表统计效应、普遍策略优势或安全保证。

## 5. 验收

提交前要求以下命令全部返回 0：

```bash
make ch07-test-local
make ch07-smoke
make check
make docs-preview-check
git diff --check
```
