# 第4章到第22章的数据身份合同传播审查

> 日期：2026-09-02
>
> 范围：第4章 `EXP-04-01` v4、第22章正文与 `EXP-22-01` v4、项目包审计器、测试、结果、实验卡、PRD 与 manifest

## 发现的问题

第4章已经把跨 split 泄漏拆为 group、原始来源、精确内容和预登记近重复簇四层，但第22章 capstone package 仍只登记 `train_groups`、`selection_groups` 和 `eval_groups`。因此同一 raw log、相同内容或已知近重复样本只要改名换组，就能通过最终交付门禁；第22章虽然 trace 到 `EXP-04-01`，却没有消费其完整合同。

## 修复后的合同

`EXP-22-01` v4 把 split 改为 train、selection、eval 三个具名分区。每个分区必须分别登记：

- `group_ids`；
- `source_asset_ids`；
- `content_fingerprints`；
- `similarity_cluster_ids`。

每个集合必须非空、元素为非空字符串且内部无重复；审计器对 train–eval、selection–eval 和 train–selection 的每个身份维度分别求交集。失败代码同时保留分区对和身份维度，避免把 selection 泄漏、同源泄漏和精确内容泄漏压成一个含义模糊的布尔值。

## 可执行证据

- 完整包登记 3 × 4 个身份集合并保持两两互斥，审计为 0 issue；
- 无效包同时注入 group/source/content/similarity 四种 train–eval 重叠，固定得到 23 个具名 issue；
- 三个回归 subcase 在 group 保持不同的情况下分别注入 source、content 和 similarity overlap，确认新门禁不依赖 group 冲突；
- selection 与 train/eval 的来源重叠另有双边界测试；
- 空集合、重复元素和空字符串均被拒绝；
- 第22章由 20 个增至 23 个单元测试，全书由 301 个增至 304 个。

## 不能外推的结论

- 审计器只比较项目包已经登记的集合，不读取图片、视频、点云或日志；
- `content_fingerprints` 的生成与 `similarity_cluster_ids` 的召回率仍属于上游第4章数据准备责任；
- 十二个集合无交集不证明统计独立、城市/天气/场景分布外，也不证明最终评测没有人工反复查看；
- 五段 trace 已人工同步为当前 `fixture-v4/v3/v5/v6/v4`，但审计器只验证 revision 非空，并不跨文件解析上游实验卡确认版本；
- 本阶段没有下载真实数据，没有运行训练、仿真、GPU、机器人或车辆实验；
- fixture 的 SHA-256 只用于稳定教学身份，不是隐私、授权、真实性或安全证明。
