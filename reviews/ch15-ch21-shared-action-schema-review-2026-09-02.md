# 第15/21章共享动作 Schema 与执行身份审查

> 日期：2026-09-02
> 范围：第15/21章正文、共享 schema、`EXP-15-01`、`EXP-21-01` v9、测试、结果、实验卡、manifest、PRD 与第22章 trace

## 发现的问题

第15章已经定义 `mobile-base-v1` 的 frame、字段、物理单位、控制频率和 clock；第21章上一阶段却另用归一化全局范围与统一 delta。这样会产生两类错误：同名 schema 在两章常量漂移，以及对 `m/s` 和 `rad/s` 取无量纲统一最大变化。

[Autoware Velocity Smoother 官方文档](https://autowarefoundation.github.io/autoware_core/main/planning/autoware_velocity_smoother/)分别登记速度、加速度、jerk、横向加速度和转向角速度约束，并使用当前/上一状态初始化。它支持“跨点约束要保留字段、单位和状态”的工程模式，但不为本书阈值定标。

## 实现与负对照

新增唯一可执行定义 `labs/shared/action_schema.py`。第15章和第21章都直接导入同一个 `MOBILE_BASE_SCHEMA`：

| 字段 | 单位 | 静态范围 | 教学单步变化上限 |
| --- | --- | --- | --- |
| `linear_velocity` | `m/s` | `[-0.5,0.5]` | `0.25 m/s/step` |
| `yaw_rate` | `rad/s` | `[-1,1]` | `0.25 rad/s/step` |

前序手工动作 `(0,0)` 下，`(0.2,-0.1)` 的变化 `(0.2,0.1)` 通过；同样静态合法的 `(0.4,-0.1)` 因线速度变化0.4触发 `action_delta_exceeded:linear_velocity`。四个单字段身份负对照分别改动当前 schema、前序单位、前序频率和 command/ack 绑定，得到四个独立原因码。

第15章新增1项测试证明它导入的共享对象包含物理单位与逐字段限值；第21章新增2项测试覆盖当前 identity 和前序 schema/unit/rate/ack。共享代码消除的是本书内部常量漂移，不认证 ack，不证明真实底盘限制、动力学、jerk、跟踪或安全。

## 一致性结果

- `EXP-21-01` 升级为 fixture v9，并绑定 `CLAIM-21-16`、`TAB-21-08`；
- 第22章 deployment/safety trace 同步为 `fixture-v9`；
- 全书当前为202条声明、110条 `result`、369个章节测试、132道练习；
- 未下载数据/checkpoint，未运行模型、GPU、仿真器、机器人或车辆。

## 验证结果

- `make smoke-all`：通过，22章共369个章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、132个折叠式自检和1161个内部目标；
- `make check`：通过，4个 Schema、68个严格规格测试与22组结果精确比对；
- `git diff --check`：通过。
