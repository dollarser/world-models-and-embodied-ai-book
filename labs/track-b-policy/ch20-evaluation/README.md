# EXP-20-01：评测协议可比性 smoke

该实验让同一个假想模型面对一张固定的 8 回合结果表，再交叉应用 `easy/full` 两种任务总体和 `goal-only/safety-aware` 两种成功定义。四格成功率为 `100% / 100% / 87.5% / 62.5%`；任务总体的变化在两种成功定义下分别是 `-12.5` 和 `-37.5` 个百分点，揭示 `-25` 个百分点的 interaction。审计器仍标记首尾协议的任务总体、成功定义和分母差异，但这些 warning 不是三个独立或可加的原因。

完整协议另报告 `8 attempted / 8 valid / 7 terminated / 1 truncated / 0 invalid`：有效 timeout 留在失败分母，具名技术无效运行会阻止聚合，不能静默删除；双真结束标志分别计数但只贡献一个 attempted episode。该 fixture 属于 E0 协议/聚合合同测试，不是 E4 部署证据。

v6 另含 10 对 candidate/baseline 结果，嵌套在 4 条重复数不均的 route 中。episode-micro 配对差为 `+0.3`，等 route macro 差为 `0.0`；代码枚举全部 `4^4=256` 个 route-level bootstrap replicate，得到手工 percentile 区间 `[-0.75,0.75]`。它还解析计算零观测事件在 `20/100/1000` 次独立暴露下的95%一侧二项上界 `13.9108%/2.9513%/0.2991%`。两者只演示统计机制：前者不提供可靠 population coverage 或策略等效证据，后者不覆盖相关 route、漏检、未见危险或真实部署风险。

它没有运行 LIBERO、MetaDrive、CARLA 或真实机器人，不能作为任何模型的 benchmark。其用途是阻止脱离协议比较成功率。

```bash
make ch20-test-local
make ch20-smoke-local
make ch20-smoke
```

数据为仓库内程序化 fixture，下载量 0，按仓库 MIT 许可发布。
