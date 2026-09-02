# 第4章 normalization provenance 审查

> 日期：2026-09-02
> 范围：第4章、`EXP-04-01 v5`、两份 metadata fixture、统计来源与重算合同
> 结论：`normalization_scope=train` 不再被当作充分证据

## 发现与修复

v4 审计器只比较 `dataset.normalization_scope == "train"`。该字符串无法证明统计资产实际来自 train split，也无法发现 mean/scale 文件被替换或数据版本变化后仍复用旧值。

v5 在 artifact 中登记 feature、population-scale 定义、source episode ID、source content fingerprint、sample count、逐维 mean 与 scale。有效 fixture 的 train episode 含三行两维 state，重算得到 count=3、mean=`[1,2]`、scale=`[sqrt(2/3),sqrt(2/3)]`，与登记值精确闭合。错误 fixture 保留原 11 类问题，并新增一个 eval source 和一组伪造统计，分别触发 `normalization_source_split` 与 `normalization_stat_mismatch`。

## 边界

content fingerprint 只绑定当前手工 metadata，不证明原始媒体真实性。三行无 mask state 也不覆盖 padding、缺失值、样本权重、角度/四元数、robust statistics、分布式 shard、在线更新、checkpoint compatibility 或真实数据分布。本阶段没有下载 LeRobot/驾驶数据，没有运行训练、GPU、机器人或车辆。

## 验收

提交前运行第4章测试与 smoke、22 组结果精确比对、严格规格门禁和 `git diff --check`；通过后只提交本阶段明确文件。
