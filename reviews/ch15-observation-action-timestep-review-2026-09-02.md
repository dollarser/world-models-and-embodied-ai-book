# 第15章观测—动作 timestep 绑定审查

> 日期：2026-09-02
> 范围：第15章正文、`EXP-15-01` v3、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

正文 `CLAIM-15-08` 已要求异步 VLA chunk 携带观测/动作 timestep，但原 `EXP-15-01` packet 只有生成 `timestamp_ms`。因此一个刚生成、墙钟年龄小于100 ms的 packet 即使基于更旧观测，仍会通过时间检查；首动作若排到错误控制槽也没有可验证字段。这是正文合同与可执行 fixture 的直接不一致。

LeRobot 官方 commit `128d3324e3202ce1fca1340fb8d7941edecce9d3` 的 [`async_inference/policy_server.py`](https://github.com/huggingface/lerobot/blob/128d3324e3202ce1fca1340fb8d7941edecce9d3/src/lerobot/async_inference/policy_server.py) 复核显示：服务端读取 observation timestamp 与 timestep，并从二者构造 chunk 内每个 `TimedAction` 的预期 timestamp/timestep。该实现锚点支持“墙钟时间与逻辑 step 身份需要同时记录”的接口事实，但不构成本书运行或安全证据。

## 修正

- packet 新增 `observation_timestep` 与 `first_action_timestep`；网关接收预登记的当前观测和首动作槽并逐项检查；
- 新增“10 ms 新鲜但 observation=40”的负对照，在预期42时返回 `observation_timestep_mismatch`；
- 新增“10 ms 新鲜、observation=42但 first action=43”的负对照，返回 `action_timestep_mismatch`；
- 对齐 packet 保持年龄50 ms与 `42→42`，三类动作头仍全部通过；
- malformed 集合由10类增至12类，`EXP-15-01` 升至 v3，新增 `TAB-15-05`、`CLAIM-15-10`、`SELF-CHECK-15-06` 与3项测试。

## 验收

```bash
make ch15-test-local
make ch15-smoke-local
make ch15-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第15章测试从15项增至18项，全书从345项增至348项；声明增至196条，其中104条为 `result`；练习/自检增至126组。

## 剩余边界

fixture 把预期 observation 与 first-action timestep 都固定为42，只验证两个精确错位类别。真实异步系统可能允许受控 lag、跳帧或未来执行槽，还需 session/boot ID、clock synchronization、队列消费进度、原子失效、ACK、认证和完整性保护。字段一致不能证明观测内容正确、动作按时到达、控制器执行或系统安全；本阶段没有运行 VLA、网络、仿真、GPU、机器人或车辆。
