# 第21章重新激活授权审查

> 日期：2026-09-01
> 范围：第21章正文、`EXP-21-01`、fixture、测试、结果、实验卡与 manifest
> 结论：将“输入恢复健康”与“允许重新激活高层策略”拆成两个独立谓词；不将手工授权信号升级为 fallback 完成或真实安全证据

## 1. 原问题

旧状态机在三次连续失败后升级为 `request_operator`，但只要收到两个连续健康包就自动返回 `policy_action`。这可以检查迟滞，却把输入健康、降级完成、状态重同步、operator 确认和重新激活授权混成一个事件。正文已经说明恢复需要 profile-specific 条件，但 fixture 没有证明这条失败路径。

## 2. 可执行负对照

- 两个分支使用相同的七步健康序列和相同的 `3 failures / 2 healthy` 迟滞。
- `health_only_negative_control` 在第 5 步第二个健康包后自动返回 `policy_action`。
- `authorization_aware` 在同一时刻保持 `request_operator`，记录 `reactivation_not_authorized`；第 6 步授权信号为真后才返回 `policy_action`。
- 配置合同拒绝授权序列长度不一致和非布尔值。
- 第21章单元测试由 14 个增至 15 个，全书由 284 个增至 285 个。

## 3. 一手资料核验

Autoware Universe 当前 `operation_mode_transition_manager` 文档区分 `IN TRANSITION` 与 `COMPLETED`，切换完成前原 operator 仍负责控制，组件还会检查 transition completion。它支持“请求、过渡、完成和控制责任不能合并”这一工程边界，但本书没有运行 Autoware，也没有把教学状态机等同于其实现。

- 一手来源：<https://github.com/autowarefoundation/autoware_universe/blob/main/control/autoware_operation_mode_transition_manager/README.md>

## 4. 证据边界

`reactivation_authorized` 是手工布尔序列，只用来检查状态机是否把授权和健康分离。它不是 operator 签名、不是认证授权协议、不表示 `controlled_stop` 或 MRM 已完成，也不验证车辆/机器人已达安全状态。真实恢复还需要本体状态、降级完成、队列清空、时钟/观测重同步、授权身份与超时/撤销语义。

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
