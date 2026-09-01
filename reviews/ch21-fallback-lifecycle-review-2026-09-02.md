# 第21章 fallback 生命周期审查

> 日期：2026-09-02
> 范围：第21章正文、`EXP-21-01` v5、fixture、测试、结果、实验卡与 manifest
> 结论：将 fallback 请求、运行、完成、超时/失败与重新激活授权拆成可审计谓词；状态报告和阈值仍是手工 fixture，不升级为物理完成或安全证据

## 1. 原问题

上一轮已经证明“输入健康”不能自动代表“允许重新激活”，但授权感知分支仍没有消费 fallback 完成/失败状态。如果实现只检查布尔授权，就可能在降级仍运行、已超时或已报失败时重新启用高层策略。

## 2. 一手资料边界

- Autoware 1.8.0 fail-safe API 把 MRM 状态分为 `NONE / OPERATING / SUCCEEDED / FAILED`，并明确 `FAILED` 时车辆仍不安全。
- 当前 Autoware Universe operation mode transition manager 区分 `IN TRANSITION / COMPLETED`，超过 `transition_timeout` 则认为 transition failure。
- 本书的 `requested` 是在 MRM 运行状态之前增加的教学控制面状态，不声称它是 Autoware message enum。

来源：

- <https://autowarefoundation.github.io/autoware-documentation/1.8.0/design/autoware-architecture-v1/interfaces/ad-api/features/fail-safe/>
- <https://github.com/autowarefoundation/autoware_universe/blob/main/control/autoware_operation_mode_transition_manager/README.md>

## 3. 可执行负对照

- 成功路径在第 2 步报告 `succeeded`，但未授权时仍拒绝；第 3 步完成与授权同时成立才允许重新激活。
- 过早授权路径的前两个 `operating` 状态产生 `fallback_not_succeeded`，第三个 operating step 超出固定上限后锁定 `failed`，原因为 `fallback_timeout`。
- 另一条路径在超时锁定后收到迟到 `succeeded`；有效状态仍是 `failed`，重新激活计数为 0。
- 显式失败路径即使后续授权为真，重新激活计数仍为 0。
- 合同拒绝非法状态、非 `requested` 起点、跳过 `operating` 直接成功、授权长度不等和布尔超时阈值。
- 第21章单元测试由 15 个增至 19 个，全书由 285 个增至 289 个。

## 4. 不可外推边界

`reported_state`、`reactivation_authorized` 和 `max_operating_steps` 都是手工离散值。fixture 不证明完成检查器正确，不执行降速/停车，不测物理可达性或真实时间，不实现授权身份、超时、撤销或重放防护，也没有验证失败后切换备用 MRM。

## 5. 验证

```text
make ch21-test-local
make ch21-smoke-local
make ch21-smoke
make smoke-all
make check
make docs-preview-check
git diff --check
```
