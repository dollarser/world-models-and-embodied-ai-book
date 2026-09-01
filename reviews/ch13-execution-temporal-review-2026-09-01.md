# 第13章执行时域与时间集成审查

> 审查日期：2026-09-01
> 范围：第13章正文、`EXP-13-01` v2、fixture、测试、结果、实验卡、manifest 与第21章接口
> 结论：动作预测长度、实际执行长度和 temporal ensemble 已分离；未把解析反例写成 ACT 性能

## 1. 发现的问题

旧正文已提醒区分 prediction horizon 与 execution horizon，但实验仍把二者合并为 `chunk_size=1/4/8`。这样同时改变模型输出长度和执行政策，无法判断 policy query—陈旧权衡来自哪里。正文还介绍 temporal aggregation，却没有公式、权重方向、逐步查询成本或可执行反例。

## 2. 一手实现核对

- LeRobot 当前 `ACTConfig` 分开 `chunk_size` 与 `n_action_steps`，并要求后者不大于前者；
- temporal ensembling 要求 `n_action_steps=1`，因为必须每一步重新查询才能形成重叠预测；
- ACT 原仓库和 LeRobot 当前实现均以 `m=0.01` 做指数权重，并让索引 0 表示最旧预测，因此正系数增加对旧预测的惯性。

这些是资料核查日期下的实现事实，版本漂移后需要重新核验。

## 3. 代码与教学修复

- `chunk_tradeoff` 固定 `prediction_horizon_steps=8`，只改变 `execution_horizon_steps=1/4/8`；
- 结果显式报告每次完整查询丢弃的预测后缀、policy query、反应延迟和两步 deadline 通过率；避免与第7章 planner 调用混名；
- 新增 oldest-first `temporal_ensemble`，并覆盖空值、非有限值、布尔值、负系数及非法执行时域；
- 稳态 `[0.8,1.2,0.8,1.2]` 的误差由 0.2 降至约 0.001；真实 target 突变时 `[0,0,0,1]` 的 ensemble 仍约为 0.246，误差约 0.754。

## 4. 边界与验收

第13章由 4 增至 10 个单元测试，全书由 166 增至 172 个。fixture 只有手工标量，没有图像、策略、控制器、时钟抖动、LeRobot、ACT、机器人、车辆或 GPU；数值只证明 smoothing 与 change-response 可能冲突。

阶段门禁包括 22 章 Docker smoke、22 组结果精确比对、4 个 Schema、18 个契约测试、22 张实验卡、3 张 benchmark card、严格文档构建和本地站点检查。
