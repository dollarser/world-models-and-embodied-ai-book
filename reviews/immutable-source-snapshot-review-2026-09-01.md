# 快速演进源码不可变快照审查

> 日期：2026-09-01
> 范围：正式 `fact` 的 GitHub 官方资产、研究雷达中的 GitHub 官方仓库、相应正文和机器门禁
> 结论：用完整 commit 固定被核查源码，拒绝把浮动 `main` 当作实现事实证据

## 1. 原有风险

日期快照只能说明作者何时看过某个仓库，不能让读者重新打开当时的内容。上游默认分支更新后，`blob/main` 和仓库首页可能继续可访问，却已不再支持正文中的具体字段、默认值、维护状态或限制。此前的证据登记能检查“有外部锚点”，但不能区分不可变源码与浮动入口。

## 2. 本轮固定的官方仓库

| 仓库 | commit | 支持的正文事实 |
| --- | --- | --- |
| Farama Gymnasium | `9e04324f6b0adbe19112206dfe247edc4142e7ec` | `TimeLimit` 保留下层 `terminated` 并独立设置 `truncated` |
| DreamerV3 | `e3f02248693a79dc8b0ebd62c93683888ddaccfe` | dynamics/representation KL 路由、`free_nats` 与 loss scale |
| WorldArena | `2da2ae253b8637ba9de3afc7bea4e087f778ee4d` | 感知质量与多种功能用途分开登记 |
| V-JEPA 2.x | `204698b45b3712590f06245fbfba32d3be539812` | V-JEPA 2.1 dense/deep-supervision 配方与公开入口 |
| Cosmos-Predict2.5 | `a2c298b0a3df3778b973fe65e9e58877b292d8a7` | 2B robot/action-cond 路径与有限维护迁移说明 |
| Cosmos 3 | `9aa98e5a0773a5558f07d2699e640858f7ca8827` | omnimodal action 接口及 action-state、3D、物理限制 |
| LeRobot | `128d3324e3202ce1fca1340fb8d7941edecce9d3` | ACT horizon/temporal ensemble 合同与 Dataset v3 存储接口 |
| Open X-Embodiment | `9eeb68b989efbcf474e8fb9019e01d02b962a604` | RLDS episode 组织及七维动作仍含 absolute/delta/velocity 差异 |

commit 由核查日的官方 Git 远端 `HEAD` 解析；正文和 `fact-evidence.json` 使用同一完整 SHA。这里只获取元数据和文本源码，没有 clone 仓库、下载模型或执行上游代码。

## 3. 机器合同

- `official_asset` 的 GitHub 证据必须使用 `blob/<40-sha>`、`tree/<40-sha>` 或 `commit/<40-sha>`；
- 研究雷达的 `official_repository` 若位于 GitHub，也必须使用完整 SHA，且 `revision` 必须包含 URL 中同一 commit；
- 新增正向测试验证固定锚点可通过，两个负向测试分别拒绝 `blob/main` 与只写日期的仓库首页；
- 论文、会议页、官方文档和供应商页面仍按其自身版本/日期合同治理，不伪装成 Git commit。

## 4. 内容边界

不可变链接证明的是“这段被审查内容不会随默认分支漂移”，不证明来源描述一定正确，不证明当前最新版仍采用相同接口，也不把 `R1` 升级为 `R2`。其他只作为扩展案例、尚未承载正式 `fact` 的仓库链接仍可逐批锁定；本轮没有声称已完成所有外部 URL 的永久归档。

## 5. 门禁计划

提交前实测结果：

- `make check` 通过：4 个 Schema、22 章、22 张实验卡、3 张 benchmark card、22 组结果精确比对和 52 个严格规格测试均通过；
- `make docs-preview-check` 通过：28 个 HTML 页面、22 个编译章节、23 个可访问 Mermaid 图和 1073 个内部目标均有效；
- 定向审计确认 `fact-evidence.json` 中不存在浮动 GitHub `official_asset`，研究雷达也不存在未锁 commit 的 GitHub `official_repository`；
- `make smoke-all` 通过：22 章共 262 个 CPU/Docker 单元测试与固定 smoke 全部完成；
- `git diff --check` 在阶段提交前作为最后一项差异门禁执行。
