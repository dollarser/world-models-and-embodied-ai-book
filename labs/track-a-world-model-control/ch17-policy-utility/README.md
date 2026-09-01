# EXP-17-01：世界模型决策效用 smoke

三个固定策略同时在“真实规则”和一个有单点盲区的“学习世界模型”中 rollout。学习模型在 9 个单步转移中答对 8 个，却把会碰撞的 `shortcut` 预测成成功到达，因而选择错误策略并造成排序反转。第一套手工 support 把 `shortcut` 标为覆盖外，gate 能拒绝它；第二套只把同一 state-action 标为覆盖内，gate 接受全部策略并再次选择碰撞捷径。v5 另把代理评测拆成 action grounding、transition、state decoder 与 outcome scorer，并冻结 `safe_route/idle` calibration panel 后才加入 `phantom_shortcut`：三个组件故障可产生相同最终代理分数，而回顾性完美排序也会在新策略进入后失败。

```bash
make ch17-test-local
make ch17-smoke-local
make ch17-smoke
```

该实验只验证 simulator gap、平均秩 Spearman、prospective policy split、support gate、policy exploitation 和单故障组件归因接口。两套 support、五个组件场景与一个 held-out policy 都是 authored negative control，不是数据密度、learned OOD detector、真实故障率、策略泛化率或可加总误差预算；实验不训练世界模型，也不估计真实机器人或自动驾驶中的效应大小。代码与程序化 fixture 按仓库 MIT 许可发布。
