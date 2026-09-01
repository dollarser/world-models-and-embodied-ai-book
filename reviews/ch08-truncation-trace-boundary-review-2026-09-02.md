# 第8章截断 bootstrap 与 λ-trace 边界审查

> 日期：2026-09-02
> 范围：第8章正文、`EXP-08-01` v4、fixture、测试、结果、实验卡、manifest 与 PRD

## 发现

原 fixture 已区分 `terminated` 与 `truncated`：自然终止关闭 value bootstrap，有效外部截断保留 `V(next)`。但 `lambda_returns` 只接收一个 discount/continuation 序列。若 replay 数组在截断行后紧邻下一 episode，非零截断 discount 会让 λ>0 的递推继续读取下一行 return，把“保留 final observation 的 value”错误扩大成“连接下一 episode 的 reward”。原单步截断测试令截断行恰好位于数组末尾，因此没有暴露该问题。

Gymnasium 官方 time-limit 指南支持 termination/truncation 的 bootstrap 区分；Pardo et al. 2018 对外部 time limit 的 partial-episode bootstrapping 给出正式讨论。本轮在此基础上进一步冻结数组接口：bootstrap discount 与递推 trace boundary 是两个信号。

## 修正

- `lambda_returns` 新增可选布尔 `trace_continuations`；默认全真仅表示单条未中断 imagined sequence；
- 新增 `lambda_trace_continuations`，对 termination 和 truncation 都关闭跨行 trace；
- 递推改为 `r_t+d_t[(1-λm_t)V_{t+1}+λm_tG_{t+1}]`；
- 两行负对照将截断行 `reward=1,V(next)=4` 与新 episode 的 `reward=100` 相邻放置；
- 正确 `d₀=1,m₀=0` 得到 target 5；遗漏 trace boundary 得到101，跨 episode leakage 为96；
- `EXP-08-01` 升至 v4，新增 `TAB-08-04`、`CLAIM-08-09`、`SELF-CHECK-08-06` 与3项测试。

## 验收

```bash
make ch08-test-local
make ch08-smoke-local
make ch08-smoke
make smoke-all
make docs-preview-check
make check
git diff --check
```

本阶段预期把第8章测试从15项增至18项，全书从336项增至339项；声明增至193条，其中101条为 `result`；练习/自检增至123组。

## 剩余边界

fixture 使用两个手工 episode 行，不估计真实 sampler 发生拼接的频率。生产系统还可能选择在 loader 层保证序列不跨边界；这种结构保证仍应有测试，且必须保留截断 final observation 供 bootstrap。这里没有训练 critic、actor 或 world model，也没有衡量 bias、稳定性、回报、仿真、GPU、机器人或车辆效果。
