# 第21章命令 epoch 与幂等边界审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文把 `(command_session_id, executor_boot_id, command_id)` 与动作 envelope 分开登记，明确序号只在 epoch 内有序；没有把重试去重写成物理副作用 exactly-once。
- **来源边界**：通过。ROS 2 Actions 只支持 goal UUID/碰撞处理的接口模式；AUTOSAR E2E R25-11 只支持 counter、ID、request/response 与 timeout 的通信保护模式，两者均未被用来背书本书阈值、实现或安全性。
- **代码一致性**：通过。`EXP-21-01` v10 对首次命令、完全重试、action/有效期改写、倒序、session/boot 错配和显式新 epoch 建立确定性状态；SHA-256 只作为 canonical envelope 比较值。
- **证据强度**：通过。结果仍标为 CPU `smoke`；内存 ledger 不声称 durable transaction、并发线性化、崩溃恢复、可信执行 ack 或实体 exactly-once。
- **教学质量**：通过。新增 `TAB-21-09`、`CLAIM-21-17`、练习10与 `SELF-CHECK-21-10`，读者可以用独立原因码复核重试和重启边界。

## 固定负对照

| case | 预期状态 | 是否新增记录 |
| --- | --- | ---: |
| 首次 command8 | `applied_once` | 1 |
| 完全相同 command8 | `duplicate_returned_cached_receipt` | 0 |
| 同 ID 改 action/有效期 | `command_identity_conflict` | 0 |
| 未登记的低序号 | `stale_or_out_of_order_command` | 0 |
| session/boot 错配 | 对应 mismatch | 0 |
| 显式新 epoch 的 command0 | `applied_once` | 1 |

## 验证记录

- 第21章单元测试：36 项通过；
- 第21/22章 smoke 结果已重新生成并与中央工件精确一致；
- 全书门禁：`make smoke-all`、`make docs-preview-check`、`make check` 与 `git diff --check` 全部通过；站点为29页、22章、23张 Mermaid、133道折叠自检和1161个内部目标，22组 smoke 与结果 JSON 精确一致，68项严格规格测试通过。

## 保留限制

物理动作与数据库提交通常不共享同一个原子事务。生产实现仍需持久化顺序、WAL/outbox 或等价恢复协议、并发仲裁、执行器侧稳定 identity 去重，以及无法确认执行状态时的本体特定 fail-safe；这些都未在本轮 CPU fixture 中实现或验证。
