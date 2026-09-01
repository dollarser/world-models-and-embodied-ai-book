# EXP-20-01：评测协议、selection bias、cluster 与零事件分析单位 smoke

该实验让同一个假想模型面对一张固定的 8 回合结果表，再交叉应用 `easy/full` 两种任务总体和 `goal-only/safety-aware` 两种成功定义。四格成功率为 `100% / 100% / 87.5% / 62.5%`；任务总体的变化在两种成功定义下分别是 `-12.5` 和 `-37.5` 个百分点，揭示 `-25` 个百分点的 interaction。审计器仍标记首尾协议的任务总体、成功定义和分母差异，但这些 warning 不是三个独立或可加的原因。

完整协议另报告 `8 attempted / 8 valid / 7 terminated / 1 truncated / 0 invalid`：有效 timeout 留在失败分母，具名技术无效运行会阻止聚合，不能静默删除；双真结束标志分别计数但只贡献一个 attempted episode。该 fixture 属于 E0 协议/聚合合同测试，不是 E4 部署证据。

v8 另含 10 对 candidate/baseline 结果，嵌套在 4 条重复数不均的 route 中。episode-micro 配对差为 `+0.3`，等 route macro 差为 `0.0`；代码枚举全部 `4^4=256` 个 route-level bootstrap replicate，得到手工 percentile 区间 `[-0.75,0.75]`。它还解析计算零观测事件在 `20/100/1000` 次独立暴露下的95%一侧二项上界 `13.9108%/2.9513%/0.2991%`，并增加 10 条 route×10 次 replay 的 pseudo-replication 负对照：假设 episode 独立时 per-episode 上界为 `2.9513%`，以 route 为独立单元时 per-new-route event-incidence 上界为 `25.8866%`。两者是不同 estimand，不能当作同一风险的窄/宽版本。

v8 还固定四个 checkpoint 的 selection/final/confirmation 三列手工分数：按 selection split 预先选择 `checkpoint-a` 后，其 final 分数为 `0.50`；错误地看完 final 再挑 `checkpoint-d` 会报告 `0.75`，但该 checkpoint 在未触碰 confirmation split 上是 `0.50`，形成 `0.25` 的 authored reuse gap。它只演示 split 角色被复用后为何不能再称为最终评测，不估计期望选择偏差、模型泛化或真实 checkpoint 优劣。所有数值只演示统计与协议机制：不提供可靠 population coverage、有效样本量、策略等效或真实部署风险证据。

它没有运行 LIBERO、MetaDrive、CARLA 或真实机器人，不能作为任何模型的 benchmark。其用途是阻止脱离协议比较成功率。

```bash
make ch20-test-local
make ch20-smoke-local
make ch20-smoke
```

数据为仓库内程序化 fixture，下载量 0，按仓库 MIT 许可发布。
