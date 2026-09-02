# 第20章自适应重试估计目标审查

> 日期：2026-09-02
> 范围：第20章正文、`EXP-20-01`/`BENCH-20-01` v11、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

原正文已在 `SELF-CHECK-20-02` 区分 per-attempt 与 best-of-two，但实验没有 attempt ledger。缺少 task/attempt 身份、触发规则和成本时，失败后重试的 task-level 成功率容易被误写成单次执行成功率，或通过成功后继续尝试、漏记第二次失败来改变分母。

## 修正

- 固定4个 task、6次实际 attempt，第二次只在首次失败后发生；
- first-attempt 与 per-attempt 成功率均为0.5，最多两次的 task success 为0.75；
- 另报2次 retry、1个 recovered task、平均1.5 attempts/task 与总成本6；
- 拒绝首次成功后重试、首次失败后缺少重试、重复身份、非法 attempt 与非有限成本；
- `EXP-20-01`/`BENCH-20-01` 升至 v11，新增 `TAB-20-08`、`CLAIM-20-14`、`METRIC-20-14` 与4项测试。

## 验收

```bash
make ch20-test-local
make ch20-smoke-local
python3 scripts/check_results.py
make check-strict
git diff --check
```

本阶段把第20章测试从32项增至36项，全书从416项增至420项；声明增至215条，其中123条为 `result`；练习仍为144组。

## 剩余边界

四个 task、outcome、重试触发和单位成本均为手工确定性 fixture。0.75 与0.5只拆开具名 estimand，不估计 iid 重试概率、真实恢复收益、时延、干预、安全风险或部署性能。没有运行 LIBERO、MetaDrive、CARLA、机器人、车辆或外部评测网络。
