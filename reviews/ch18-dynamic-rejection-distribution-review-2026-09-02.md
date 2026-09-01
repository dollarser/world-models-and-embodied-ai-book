# 第18章 dynamic rejection 分布审查

> 日期：2026-09-02
> 范围：第18章正文、`EXP-18-01` v3、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

第18章已说明全成功/全失败 rollout group 的 leave-one-out advantage 为零，并警告 dynamic sampling 会改变任务分布；原 `EXP-18-01` 只验证零信号，没有记录 attempted、rejected 与 used 三套分母。因此读者仍可能只看训练 batch，误把“被选择后的 context 组成”当作环境或任务原始分布。

RIPT-VLA 论文的 Algorithm 1 在 `all A = 0` 时执行 dynamic rejection，并继续采样直到收集满 rollout dataset。作者 commit `440990e8864e12e4578b490ff6359e4f2c49ae3e` 的 [`rollout_generator.py`](https://github.com/Ariostgx/ript-vla/blob/440990e8864e12e4578b490ff6359e4f2c49ae3e/ript/algos/rl_optimizers/rollout_generator.py)也在一组 success 全0或全1时丢弃该样本，只把非全同组计入 valid sample。该一手来源支持审查选择分母，不等于本书执行或复现 RIPT-VLA。

## 修正

- 新增四个手工 context group：一个全成功 easy、一个全失败 hard、两个 mixed-outcome medium；
- `dynamic_rejection_report` 分别输出 attempted/used/rejected group、attempted/used rollout、接受率、分层分布与分层拒绝率；
- 固定结果为4组尝试、2组拒绝、2组使用，12条 rollout 中6条进入 used；
- attempted 的 easy/medium/hard 为25%/50%/25%，used 为0%/100%/0%；
- `EXP-18-01` 升至 v3，新增 `TAB-18-05`、`CLAIM-18-10`、`SELF-CHECK-18-06` 与3项测试。

## 验收

```bash
make ch18-test-local
make ch18-smoke-local
make ch18-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第18章测试从11项增至14项，全书从348项增至351项；声明增至197条，其中105条为 `result`；练习/自检增至127组。

## 剩余边界

easy/medium/hard 标签、reward 向量、context 数与顺序都是手工构造。fixture 没有反复采样到固定 batch size，不估计额外 rollout 成本、真实 task prevalence、policy 更新后的采样漂移、梯度偏差、收敛或策略性能；也没有运行 VLA、RIPT-VLA、LIBERO、仿真、GPU、机器人或车辆。真实报告还应保存每次 context/task/init identity、attempt index、拒绝原因、重采次数和按训练迭代变化的分层统计。
