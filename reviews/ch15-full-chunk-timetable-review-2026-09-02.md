# 第15章完整 action chunk timetable 审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文把 packet 生成时间、观测 timestep、首动作 timestep 与完整 action timetable 分为四个接口，不再用首动作对齐代表整个 chunk 对齐。
- **实验合同**：通过。`EXP-15-01` v4 固定三步动作、首槽42和连续整数槽规则；合法序列为 `(42,43,44)`。
- **负对照**：通过。`(42,42,44)` 与 `(42,44,45)` 的首动作槽都正确，但分别重复/跳过内部槽，均以 `action_timestep_sequence_noncontiguous` 拒绝。
- **代码一致性**：通过。packet factory 自动生成完整 timetable；网关另拒绝缺失、长度错位、非整数或负值序列。malformed packet 集合由12增至14。
- **教学质量**：通过。新增 `TAB-15-06`、`CLAIM-15-11`、练习7与 `SELF-CHECK-15-07`，并贯通自动驾驶轨迹点的完整时间向量检查。
- **证据边界**：通过。连续整数槽只是教学调度身份，不证明真实墙钟执行、队列消费、ACK、速度/加速度/jerk、碰撞或功能安全。

## 固定对照

| packet | first slot | full timetable | result |
| --- | ---: | --- | --- |
| valid | 42 | `(42,43,44)` | accepted |
| duplicate | 42 | `(42,42,44)` | rejected |
| skipped | 42 | `(42,44,45)` | rejected |

## 验证范围

- 第15章单元测试：23项；
- smoke 与中央结果：要求精确一致；
- 全书目标计数：210条声明、118条结果、400个章节测试、140道练习；
- 完整门禁在提交前运行；没有 VLA/VLM、数据、仿真、GPU、机器人或车辆。
