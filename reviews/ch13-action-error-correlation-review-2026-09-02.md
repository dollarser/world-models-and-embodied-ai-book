# 第13章动作误差时间相关性与查询语义审查

> 日期：2026-09-02
> 范围：第13章正文、`EXP-13-01` v3、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

原 fixture 把固定 `+0.02` 动作误差送入单位增益标量积分器，但输出字段和读者说明称其为“闭环状态误差”。代码没有观测依赖反馈或重新计算策略，因此该数值只能证明一种误差传播可能性，不能作为闭环策略性能。原正文还把动作块的联合预测、减少高频推理和 temporal ensembling 合并为一项主要收益；实际上，只有 `K_exec>1` 的执行政策减少查询，ACT temporal aggregation 则把 query frequency 设为1以形成重叠预测。

[ACT 原仓库固定快照](https://github.com/tonyzhaozh/act/blob/742c753c0d4a5d87076c8f69e5628c79a8cc5488/imitate_episodes.py)显示：非集成路径按 `num_queries` 查询，temporal aggregation 路径改为每步查询，并按查询时间缓存对同一动作时刻的预测。该源码事实只约束协议解释，不代表本书运行了 ACT。

## 修正

- 将 `closed_loop_final_state_error` 改为 `integrated_final_state_error`，并把 amplification 改为带步数语义的 `integration_gain_steps`；
- 新增持续同号与正负交替误差对照：两者 20 步 RMSE/MAE 都是 `0.02`，最终积分状态误差为 `0.40/0`，交替序列最大瞬态偏移为 `0.02`；
- 明确 `TAB-13-01` 的扰动枚举是初始查询后的15个动作边界，不包含可立即响应的 `t=0`；
- 明确动作块联合预测不必然减少查询，`K_exec>1` 与逐步 temporal ensembling 是不同执行模式；
- `EXP-13-01` 升至 v3，新增 `TAB-13-03`、`CLAIM-13-07`、`SELF-CHECK-13-05` 与3项测试。

## 验收

```bash
make ch13-test-local
make ch13-smoke-local
make ch13-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第13章测试从10项增至13项，全书从339项增至342项；声明增至194条，其中102条为 `result`；练习/自检增至124组。

## 剩余边界

两个误差序列是作者构造的确定性标量，既没有反馈控制，也没有学习策略、接触动力学、动作限幅、观测延迟或状态相关误差。相同 RMSE 的对照只证明逐点幅值指标遗漏时间结构，不能证明持续误差一定更危险、交替误差一定安全或真实系统线性积累。固定周期 reaction-delay 模型也没有事件触发中断、墙钟推理抖动或独立安全层；本阶段未下载数据、运行 LeRobot/ACT、仿真、GPU、机器人或车辆。
