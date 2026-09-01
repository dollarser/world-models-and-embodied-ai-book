# 第17章 coverage 内模型错误负对照审查

> 审查日期：2026-09-01
> 范围：第9→17章真实性回查接口、`EXP-17-01` v3、实验卡、fixture、测试与中央结果

## 1. 发现的问题

原 `EXP-17-01` 只有一种 support 声明：唯一错误动作 `shortcut` 恰好处于 support 外，因此 gate 拒绝它并把 exploitation regret 从 1.85 降为 0。正文已经提示 gate 无法发现 coverage 内错误，但没有可执行负对照；读者仍可能把这个完美结果误读为“通过 support gate 即可信”。

## 2. 受控负对照

v3 保持以下对象完全不变：三条策略、learned transition、真实规则、模型 return、策略排序和 tie-breaking。唯一处理变量是手工 support 声明：

- `out_of_support_error` 不包含 `(position=0, shortcut)`：拒绝 1 条策略，选择 `safe_route`，真实终点 goal，regret 0；
- `in_support_model_error` 加入该 state-action：拒绝 0 条策略，仍选择 `phantom_shortcut`，真实终点 collision，regret 1.85。

这个 paired fixture 证明的是逻辑边界：coverage membership 只能回答“是否满足这套 coverage 定义”，不能回答 transition、reward、termination 或风险预测是否正确。它不估计真实 coverage quality，也不比较 learned OOD estimator。

## 3. 第9→17章证据闭环

第9章把策略用途对应到 E3 排序和 E4 目标环境 outcome；第17章现在用同一个错误展示三层输出：model return、coverage gate decision、known-rule outcome。support 外拒绝可以作为保护层，但 support 内负对照仍须由独立真实性锚点暴露。

MOPO 一手论文用于说明模型不确定性惩罚和离线分布偏移的代表性接口，不为本书 fixture 数值背书。本书没有复现 MOPO，也没有把 support membership、ensemble disagreement 或 uncertainty penalty 写成真实性证明。

## 4. 代码与输入合同

fixture 新增参数化 support 声明、结构验证和 `support_gate_audit`。无效类型、布尔位置、未知动作和终点位置 support 均被拒绝。新增 2 个测试后，第17章由 10 个增至 12 个，全书由 282 个增至 284 个。

## 5. 保留边界

两套 support 都是 authored metadata；真实环境是手工 corridor 规则。没有神经世界模型、数据密度估计、概率校准、仿真器、GPU、机器人、车辆或安全认证。regret 数值无物理单位，也不是现实失效率。

## 6. 验收

提交前要求以下命令全部返回 0：

```bash
make ch17-test-local
make ch17-smoke
make smoke-all
make check
make docs-preview-check
git diff --check
```
