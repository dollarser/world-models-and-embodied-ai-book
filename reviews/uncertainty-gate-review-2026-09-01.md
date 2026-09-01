# 跨章不确定性门禁审查：第5、9、21章

> 日期：2026-09-01
> 范围：第5章 epistemic 概念、第9章 OOD 评测、第21章执行网关与 `EXP-21-01`
> 目标：让“不确定时拒绝”从一句建议变成版本化、可评测、可执行的合同

## 审查结论

原书已多次要求 OOD 拒绝，但存在两处断点：第9章没有定义阈值变化时怎样同时报告执行覆盖与留下的失败，第21章 packet gate 也没有 uncertainty score 或专用原因码。此次把三章连接为：

```text
第5章：区分 aleatoric 与 epistemic
  → 第9章：冻结 score 后评估 risk–coverage、失败捕获和 fallback 后果
  → 第21章：锁定 estimator/calibration 版本，以预注册阈值决定执行或降级
```

## 准确性边界

- uncertainty score 不自动是概率；必须记录定义、方向、估计器和校准协议版本。
- OOD AUROC 只反映冻结总体上的排序，不直接给出接受样本风险或 fallback 后果。
- selective risk 只在被接受样本上定义；coverage 为零时不能报告零风险。
- 更严格的阈值不保证真实风险单调下降，因为 estimator 可能低分错排危险样本。
- 阈值在 calibration split 选择，在锁定的 ID/shift/OOD/stress split 评估；不能在测试集挑最佳点。
- 网关拒绝只验证合同路径，不能证明 estimator、fallback 或整个系统安全。

上述 risk–coverage 定义与拒绝选项参考 Geifman & El-Yaniv 的选择性分类工作；多阈值指标边界参考 Traub et al. 2024。两者是评测设计来源，不是本书复现结果。

## EXP-21-01 增量

`ActionPacket` 新增必填 `uncertainty_score` 与 `uncertainty_revision`，`GateConfig` 新增 `[0,1]` 范围内的 `max_uncertainty_score` 和预期 revision。网关区分：

- `invalid_uncertainty_score`：非数值、非有限或越出合同范围；
- `uncertainty_exceeds_limit`：合法分数超过冻结工作点；
- `uncertainty_revision_mismatch`：packet 与部署配置使用不同估计器/校准合同版本。

七个 packet 中仅 healthy 通过，六类故障分别触发唯一原因码。另用六个手工 `(score, failure)` 对得到：

| 阈值 | coverage | 接受 failure rate | 拒绝捕获 failure 比例 |
| ---: | ---: | ---: | ---: |
| 0.5 | 0.5 | 0.0 | 1.0 |
| 0.7 | 0.666667 | 0.25 | 0.666667 |

这些值只验证公式、分母与 gate 连接，不代表真实 OOD estimator 排序或校准。

## 检查记录

```text
make ch21-test-local       # 9 tests
make ch21-smoke-local      # packet gate 与 selective metrics 通过
make check-local           # manifest、实验卡、22 组结果一致
make ch21-smoke            # Docker 内 9 tests 与结果通过
make smoke-all             # 22 章 Docker CPU smoke，144 tests
make check                 # 严格 schema、结果和服务检查通过
make docs-preview-check    # 当前累计 27 HTML、22 章、986 个内部目标
git diff --check           # 通过
```

阶段提交前已执行第21章 Docker smoke、全书 Docker CPU smoke、严格 `make check` 和站点检查。

## 保留限制

- 没有真实 estimator、calibration split、OOD 数据或 learned model。
- 没有执行 fallback 控制器，也未衡量拒绝导致的任务成本。
- M 档后续应在通用仿真中保存逐 episode score、失败类型、阈值选择记录和 fallback 闭环结果；自动驾驶还需按道路场景与严重度分桶。
