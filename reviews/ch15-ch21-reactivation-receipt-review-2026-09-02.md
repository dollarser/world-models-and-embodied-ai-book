# 第15/21章重新激活 receipt 交叉审查

> 日期：2026-09-02
> 范围：第15章动作 packet、第21章正文、`EXP-21-01` v6、测试、结果、实验卡、PRD 与 manifest
> 结论：把“授权为真”细化为绑定、时效、序号和单次消费合同；仍不把手写身份或内存状态升级为认证、完整性或安全证据

## 1. 原问题

第15章已经用共同 clock、半开有效期和单调 `command_id` 拒绝单会话内的旧动作命令；第21章前两轮则仍以 `reactivation_authorized: bool` 隔离健康、fallback 完成与授权。这个布尔基线适合证明谓词独立，却无法回答授权属于哪次 fallback、允许哪个目标模式、由谁声明、何时失效以及是否已被消费。

## 2. 一手资料与适用边界

- RFC 9396 用 actions、locations、identifier 与 privileges 等授权细节限制对象和动作。
- RFC 9449 要求 proof 具有唯一 `jti`，并讨论 creation-time window、server nonce 与 duplicate rejection。
- RFC 9700 建议 access token 做 audience restriction，并用 sender-constrained token 等机制降低 replay 风险。

来源：

- <https://www.rfc-editor.org/rfc/rfc9396.html>
- <https://www.rfc-editor.org/rfc/rfc9449.html>
- <https://www.rfc-editor.org/rfc/rfc9700.html>

这些来源是 OAuth/互联网授权规范，不是机器人、车辆、ISO 26262 或 ISO 21448 标准。本书只借用对象绑定、时效和 replay 的协议形状；fixture 没有实现 OAuth、proof-of-possession、签名、sender constraint 或可信身份系统。

## 3. 可执行负对照

- `ReactivationReceipt` 固定 `receipt_id / approver_id / fallback_run_id / target_mode / issued_step / valid_until_step / sequence / decision`。
- 有效区间为 `[issued_step, valid_until_step)`；未来签发与过期使用同一时间原因族。
- 声明 approver 必须出现在手写 allowlist，但代码和正文都不称其为 authenticated principal。
- 唯一有效 receipt 先通过；模拟消费后，相同 ID 与序号同时触发 `receipt_already_consumed` 和 `replay_or_out_of_order_receipt`。
- 另有 run、target、approver、decision 和旧序号的隔离负例。9 例中 1 例允许、8 例拒绝。
- 新增 4 个单元测试，第21章由 19 个增至 23 个，全书由 289 个增至 293 个。

## 4. 不可外推边界

验证器是纯函数，消费集合与最后序号由 audit 在单进程内手工更新。它不提供身份认证、消息签名、防篡改、撤销、持久化、跨重启 replay 防护、并发原子消费或密钥管理。receipt 即使通过也不证明 fallback `succeeded`、本体达到安全状态、队列已清空、时钟已重同步或重新激活满足功能安全要求。

## 5. 验证

```text
make ch21-test-local
make ch21-smoke-local
python3 scripts/check_results.py
make check
make ch21-smoke
make smoke-all
make docs-preview-check
git diff --check
```
