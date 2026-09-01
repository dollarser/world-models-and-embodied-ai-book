# 第5章诊断增强审查：条件、覆盖与越界生成

> 日期：2026-09-01
> 范围：第5章、`EXP-05-01`、实验卡、结果与跨章状态
> 目标：把生成模型谱系从“知道方法名称”提升为“能定位失败类型”

## 审查结论

第5章原有 VAE、离散 latent、自回归、masked prediction、diffusion 和 flow matching 的基本边界正确，一手来源和跨章接口没有阻断问题。主要缺口是诊断流程不足：条件忽略、模式坍缩和越界生成可能在不同指标下互相掩盖，原 fixture 只能证明均值落在多模态 support 外。

本轮新增五步诊断树：数据合同、条件使用、coverage/validity、概率/样本一致性、自由 rollout/下游用途。正文同时补充以下边界：

- total variation 只能量化条件变化后的分布差异，不能证明响应方向正确；
- 连续 density/NLL 会受单位、离散化和预处理影响，只能在共同输出合同下比较；
- 有限样本的“观察 support”不是未知真实连续分布的完整 support；
- 多次采样主要展示模型学到的 aleatoric 分布，不自动揭示 epistemic/OOD 无知；
- 自动驾驶多未来进入风险约束规划，覆盖不足则进入拒绝、降级或额外感知。

## EXP-05-01 增量

程序化分布增加三类反例：

| fixture | 诊断结果 | 含义 |
| --- | --- | --- |
| `context_ignored` | context TV `0.0` | 改变上下文但预测分布不变 |
| `collapsed` | observed-mode recall `0.5` | 第二个已观察 mode 概率低于 1% 阈值 |
| `hallucinated` | out-of-observed-support mass `0.1` | 给手工样本未观察的中间值分配 10% 质量 |
| faithful conditioned | context TV `0.5`、mode recall `1.0` | 只作为解析对照，不是学习模型性能 |

新增 `total_variation_distance` 和 `support_diagnostics`，对归一化、空观察集、阈值和布尔输入执行显式拒绝。第5章测试由 7 个增至 10 个；实验卡数据版本升级为 `v2`，`CLAIM-05-07`、结构化结果和限制已同步。

## 已执行检查

```text
make ch05-test-local       # 10 tests
make ch05-smoke-local      # 解析结果与故障断言通过
make check-local           # 22 张实验卡与 22 组结果精确一致
make docs-build            # MkDocs strict 通过
make docs-preview-check    # 27 HTML、22 章、979 个内部目标
make ch05-smoke            # Docker 内 10 tests 与结果通过
make smoke-all             # 22 章 Docker CPU smoke，142 tests
make check                 # 严格 schema、结果与服务检查通过
git diff --check           # 通过
```

阶段提交前已再次执行第5章 Docker smoke、全书 `make check` 与全书 Docker CPU smoke。它们不下载外部数据，也不需要 GPU。

## 保留限制

- 没有训练 VAE、tokenizer、diffusion、flow 或视频模型；不能外推生成质量、速度或显存。
- 离散 TV 与观察 support 诊断是教学接口，真实连续/高维数据需要任务相关距离、密度估计或约束检查。
- 当前没有为 epistemic 不确定性实现 ensemble/OOD fixture；后续可与第9章和第21章的拒绝门禁联合扩展。
