# 第21章运行时队列与降级状态审查

> 日期：2026-09-01  
> 范围：第21章正文、`EXP-21-01`、fixture、测试、结果、实验卡与 manifest  
> 结论：补齐 deadline burst、异步 chunk 新鲜度与 fallback 升级/恢复机器合同；真实实时性、MRM 可达性和安全状态不升级

## 1. 发现的问题

正文已经要求 p99、连续 deadline miss、action queue 新鲜度、连续 fallback 升级和恢复规则，但旧 fixture 只报告 mean/p95/max/miss rate，并逐包返回一个 fallback 标签。该实现无法证明相同总体时延摘要下的 burst 差异，也无法区分“队列为空”和“队列非空但动作陈旧”，更没有表达降级模式的迟滞恢复。

## 2. 代码与结果修正

- `latency_summary` 新增 nearest-rank p99、miss count 和 maximum consecutive misses。
- 两组固定序列具有相同 mean `40 ms`、p95/p99/max `80 ms` 和 miss rate `2/6`，但最大连续 miss 为 `2` 与 `1`。
- 八步 `ActionChunk` schedule 使用 exclusive `valid_until_step`，报告 6 次 policy action、1 次 `stale_chunk`、1 次 `queue_underflow` 和 1 个晚到 chunk。
- 六步 fallback 状态机在三次连续拒绝时由 `controlled_stop` 升级到 `request_operator`；升级后需要两次连续健康才恢复 policy，避免一次健康脉冲导致 mode flapping。
- 第21章测试由 9 增至 14，全书由 241 增至 246。

## 3. 一手资料核验

- LeRobot 当前 inference/async 文档明确使用后台 chunk 生产、队列阈值和控制 FPS，并提示生产/消费速度失配会耗尽队列。
- ROS 2 QoS 与实时设计资料区分通信 deadline 和端到端确定性，实时路径仍需处理 page fault、动态分配和阻塞同步。
- Autoware 当前 operation mode 与 command mode 文档区分模式请求、`In Transition`、完成检查、控制责任，以及 emergency/comfortable stop 等不同 MRM source。

这些上游接口均未在本书运行，不构成本书实时或道路安全结论。

## 4. 边界

所有时间和 step 都是手工离散值；没有墙钟、clock synchronization、线程、调度器、网络、ROS、模型、执行器或车辆。状态机只验证字符串模式与阈值逻辑，不验证 controlled stop 的动力学可达性、operator availability、MRM 完成或恢复安全。

## 5. 验证

```text
make ch21-test-local
make ch21-smoke-local
make smoke-all
make check
make docs-build
make docs-preview-check
git diff --check
```
