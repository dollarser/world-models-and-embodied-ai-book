# 第16章 action-window 有效暴露审查（2026-09-02）

## 审查结论

- **问题定位**：通过。dataset/episode/transition 权重只定义原始抽样分母，不能证明各来源真正产生了可进入 loss 的完整 action window。
- **固定反例**：通过。short 来源含1条长度2 episode，long 来源含3条长度4 episode；固定 `H=3`、stride one、drop-tail 后，short 贡献0个窗口，long 贡献6个。
- **分母一致性**：通过。long 的 raw-transition 暴露为12/14即85.7143%，合格窗口暴露为6/6即100%；两者没有被混称为随机 batch 或梯度暴露。
- **实现边界**：通过。fixture 显式拒绝非正/布尔 horizon 与全来源零窗口；没有实现 padding、mask、过滤、sampling replacement、distributed shard 或 gradient weighting。
- **教学与驾驶迁移**：通过。新增 `TAB-16-06`、`CLAIM-16-10`、练习7与 `SELF-CHECK-16-07`，并说明短促急刹/接管片段可能被窗口策略系统性删除。

## 验证范围

- 第16章单元测试：19项；
- smoke 与中央结果要求精确一致；
- 全书目标计数：211条声明、119条结果、404个章节测试、141道练习；
- 完整门禁在提交前运行；没有真实数据、训练、GPU、仿真、机器人或车辆。
