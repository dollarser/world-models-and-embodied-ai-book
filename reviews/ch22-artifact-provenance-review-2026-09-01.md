# 第22章 Artifact Provenance 与独立评测审查

> 审查日期：2026-09-01
> 审查基线：`be77895`
> 范围：第22章正文、`EXP-22-01` v3、项目包 fixture、测试、结构化结果、实验卡与 manifest
> 结论：S 档项目包审计从字段存在性升级为可校验身份与证据关系；不改变 GPU、仿真、机器人或车辆的未验证状态

## 1. 为什么需要二次审查

旧版能够发现缺字段和跨章 trace 断裂，但 artifact 只要是非空字符串就算存在，独立评测和 safety gateway 也主要依赖布尔标记。这允许三个不可靠包通过：文件名存在但内容已漂移，最终 test route 被用于选模型，以及安全门虽然写成 `true` 却没有失败证据和 fallback。

本轮用以下一手规范校准边界：

- [ACM Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current)明确区分 artifact 可获取、功能/复用评审与结果复现/重复；
- [SLSA Provenance v1.2](https://slsa.dev/spec/v1.2/provenance)用 artifact digest 绑定产物身份，并描述产物怎样生成；
- [RO-Crate 1.2](https://www.researchobject.org/ro-crate/specification/1.2/introduction.html)把数据、代码、工作流和 provenance 组织成 research object；
- [NeurIPS Paper Checklist](https://blog.neurips.cc/2021/03/26/introducing-the-neurips-2021-paper-checklist/)要求透明登记训练/评测细节、代码、数据、指令与限制。

因此本章明确：digest 一致只说明本次登记内容没有漂移，不证明内容正确、许可有效或结果已复现。

## 2. 合同修复

完整 fixture 现在要求：

1. train、selection、eval route 三组两两互斥，避免用 test 选择 checkpoint、阈值或 prompt；
2. 五类 artifact 均绑定 `uri + sha256 + producer_stage + claim_ids`，claim ID 和生产阶段使用精确规则；
3. payload 必须存在且重算摘要一致，篡改结果触发 `artifact_digest_mismatch:result`；
4. 五段 trace 的 `EXP/BENCH` 章节号、revision、decision 和依赖必须一致；
5. 独立评测同时登记训练独立、协议预先冻结和 evaluator artifact；
6. 失败注入登记预期问题、实际问题与 failure record；
7. driving safety gateway 绑定部署 trace、failure record 和非空 fallback modes；
8. S/M、L1、L2 分别执行 CPU、最多 1×24 GB、最多 2×80 GB 的档位语义。

资源语义的修复尤其重要：1×80 GB 可以是 L2，但不能包装成 L1；旧版全局阈值会错误拒绝合法 L2 单卡路径。

## 3. 结果与边界

- 完整固定包保持 0 issue；
- 故意无效包由 16 增至 20 个具名 issue；
- 完整包校验 5 个 artifact binding 和 2 个失败注入；
- 第22章由 12 增至 20 个单元测试，全书由 246 增至 254 个；
- 新测试覆盖 payload 篡改、非法 claim/producer、selection/eval 泄漏、trace revision/章节身份、评测冻结/evaluator 绑定、弱安全门、失败注入未复现，以及 L1/L2 档位边界。

所有 payload 仍是内存中的固定短文本。审计器没有遍历真实项目目录、解析容器镜像或数据集、执行复现命令，也没有建立 ACM `Results Validated` 含义上的独立复现。

## 4. 门禁

本阶段要求以下命令全部返回 0：

```bash
make ch22-test-local
make ch22-smoke-local
make smoke-all
make check
make docs-build
make docs-preview-check
git diff --check
```

GPU、大型数据下载、MetaDrive/CARLA、机器人、车辆和真实部署均未运行；这些状态保持 `pending` 或未验证。
