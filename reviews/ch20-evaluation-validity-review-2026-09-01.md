# 第20章评测有效性与证据层级审查

> 日期：2026-09-01  
> 范围：第20章正文、`EXP-20-01`、`BENCH-20-01`、fixture、测试、结果与 manifest  
> 结论：修复证据层级越界，补齐协议交互、评测泄漏、分层统计与最新一手案例；不升级真实 benchmark 或部署证据状态

## 1. 关键问题

旧 benchmark card 把手工八行 outcome 表同时标为 E0 与 E4。按本章自己的证据阶梯，E4 要求限定运行设计域中的长期部署事件率与安全流程；固定表格只能检查协议、分母和聚合器，因此应严格归入 E0。旧实验还只比较两个同时改变任务总体与成功定义的端点，三个 comparability warning 容易被误读为三个独立、可加的原因。

## 2. 修正

- `BENCH-20-01` 的 `evaluation_layers` 和全部 fixture metric 统一改为 E0；正文、README 与卡片明确禁止把它写成 E4 部署证据。
- 协议扩为 `easy/full × goal-only/safety-aware` 四格。固定成功率为 `1.0 / 1.0 / 0.875 / 0.625`。
- 条件任务总体效应为 `-0.125 / -0.375`，条件安全规则效应为 `0 / -0.25`，interaction 为 `-0.25`。这些是 authored rows 上的精确算术对照，不是总体因果效应。
- 保留 timeout、invalid attempt 和 Wilson 区间合同；新增两项测试覆盖四格和 interaction，全书测试数由 239 增至 241。

## 3. 内容增强

- 统计设计补入 independent unit、cluster bootstrap、paired comparison、macro/micro aggregation、adaptive stopping 与多重选择偏差。
- 有效性补入 checkpoint/任务/资产泄漏、人工裁决盲法、闭源 API 版本漂移。
- 一手资料复核 LIBERO、SimplerEnv、RoboArena 与 CARLA Leaderboard 2.1。特别说明 CARLA 的 route-level 组合与 global aggregation 不同，且 2.1 penalty 公式相对 2.0 已变化，因此必须锁定 leaderboard/scorer 版本。

## 4. 边界

没有下载或运行 LIBERO、SimplerEnv、RoboArena、MetaDrive、CARLA，没有真机、道路、GPU 或真实策略数据。Wilson 区间仍使用独立 Bernoulli 教学假设；cluster/paired 方法只在正文解释，没有伪造样本或区间。`reviewed` 仅覆盖正文和 S 档机器合同。

## 5. 验证

```text
make ch20-test-local
make ch20-smoke-local
make smoke-all
make check
make docs-build
make docs-preview-check
git diff --check
```
