# 全书章节优化完成度审查

> 日期：2026-09-02
> 范围：22 章正文、manifest、实验卡、S 档实验与结果、审查记录、PRD 执行流程和读者实现来源
> 结论：当前 22 章 S 档优化、机器合同与文档代码一致性满足发布候选门；M/L、GPU、真实数据、仿真、硬件和人工可访问性验收保持未完成边界

## 完成要求与当前证据

| 要求 | 当前权威证据 | 判定 |
| --- | --- | --- |
| 章节内容准确性与丰富性 | manifest 含连续 1–22 章；每章 content/code/consistency/teaching 四类状态均为 `passed`；PRD 执行流程对 22 章均有具名增强记录 | 当前 S 档完成 |
| 声明与图表一致性 | manifest 登记 222 个唯一 claim 与 138 个唯一 `FIG/TAB`，目标 ID 均存在于对应正文 | 完成 |
| 实验可执行与结果可追踪 | 22 张实验卡与 22 个中央 smoke JSON 一一对应；所有实验仍如实标记为 `smoke` | 当前 S 档完成 |
| 结果一致性 | `scripts/check_results.py` 要求 22 组脚本输出与登记 JSON 精确相等 | 待本阶段门禁确认 |
| 来源不可变性 | 读者文档不存在 GitHub `blob/tree main/master` 实现链接；快速演进实现断言锁完整 commit | 完成 |
| 发布规格与站点 | Schema、manifest、版本同步、审查索引、Markdown、内部目标、Mermaid 与 MkDocs 由严格/站点门禁覆盖 | 待本阶段门禁确认 |
| 工作树边界 | 只提交本阶段审查记录、索引与执行流程；`AGENTS.md`、`BOOK_HANDOFF.md`、`BOOK_QUEUE.md` 保持未跟踪 | 待提交确认 |

## 生命周期与未验证范围

当前 22 个实验均为 `smoke`，不是 `experimented` 或 `reproducible`。6 章不需要 GPU，16 章 GPU 状态为 `pending`。这不否定 S 档的零下载、CPU、标准库或受限容器复现价值，但禁止把以下事项写成已完成：

- M/L 训练、论文指标复现或跨 seed 统计；
- 大型数据下载、真实 LeRobot/驾驶数据审计或第三方许可验收；
- GPU 显存、吞吐、时延、仿真、机器人、车辆或端到端安全结果；
- 部署、截图式多尺寸检查、深浅色、键盘或屏幕阅读器人工验收。

这些项目是明确的可选/外部资源路径和发布操作，不是当前 22 章 S 档优化完成的替代证据。未来若启动其中任一项，必须使用新实验 ID 或升级相应生命周期，并重新运行其范围匹配的验收。

## 最终门禁

本阶段提交前必须全部返回 0：

```bash
make smoke-all
python3 scripts/check_results.py
make check-strict
make docs-build
make docs-preview-check
git diff --check
```

门禁通过只能证明仓库当前提交候选的 S 档代码、结构化结果、规格和生成站点一致；不能扩展为上述未验证范围的证据。
