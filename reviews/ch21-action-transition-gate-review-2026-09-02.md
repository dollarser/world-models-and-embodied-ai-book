# 第21章动作跃迁门禁审查

> 日期：2026-09-02
> 范围：第21章正文、`EXP-21-01` v8、测试、结果、实验卡、manifest、PRD 与第22章 trace

## 问题与证据

旧网关能拒绝 NaN/Inf 和超过 `[-1,1]` 的动作，却把每个当前向量孤立检查。两个端点都合法时，从上一条实际命令到当前命令的突变仍可能绕过静态范围门。

- [Autoware Velocity Smoother 官方文档](https://autowarefoundation.github.io/autoware_core/main/planning/autoware_velocity_smoother/)分别约束 velocity、acceleration、jerk、lateral acceleration 与 steering angle rate，并按当前或上一规划状态设置初值；它支持“状态约束不能退化为端点范围”的工程模式。
- 该来源不为本书的归一化 `0.25/step` 定标，也不能证明任意车辆或机器人的物理限制。

## 实现与边界

`GateConfig.max_action_delta_per_step` 默认关闭，只有本体 profile 显式配置后才启用。启用时，网关要求 `AppliedAction` 维度有限、步号恰为当前步减一；缺历史、错维度、非有限值或错步均 fail closed。固定负对照在同一前序 `(0,0)` 下得到：

| 当前向量 | 静态范围 | 最大绝对变化 | 结果 |
| --- | --- | ---: | --- |
| `(0.2,-0.1)` | 通过 | 0.2 | allow |
| `(0.8,-0.8)` | 通过 | 0.8 | `action_delta_exceeded` |
| `(0.8,-0.8)`，无历史 | 通过 | 不可计算 | `missing_previous_applied_action` |

四个新增测试覆盖合法端点突变、平滑通过、缺失/错步历史、非法阈值和维度错配。这里的 `AppliedAction` 仍是作者手写记录，不是经过认证、持久化并绑定执行器反馈的 ack；离散归一化差值也不是物理 acceleration、jerk、可达性、跟踪稳定或安全证明。

## 一致性结果

- `EXP-21-01` 升级为 fixture v8，并由 `CLAIM-21-15`、`TAB-21-07` 和实验卡反向绑定；
- 第22章 deployment/safety trace 同步为 `fixture-v8`，描述增加 cross-step discontinuity；
- 全书当前为201条声明、109条 `result`、366个章节测试、131道练习；
- 未下载数据/checkpoint，未运行模型、GPU、仿真器、机器人或车辆。

## 验证结果

- `make smoke-all`：通过，22章共366个章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、131个折叠式自检和1161个内部目标；
- `make check`：通过，4个 Schema、68个严格规格测试与22组结果精确比对；
- `git diff --check`：通过。
