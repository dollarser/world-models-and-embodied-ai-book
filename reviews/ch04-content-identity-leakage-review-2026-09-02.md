# 第4章内容身份与近重复泄漏审查

> 日期：2026-09-02
>
> 范围：第4章正文、`EXP-04-01` v4、两份 metadata fixture、审计器、测试、结果、实验卡、PRD 与 manifest

## 审查结论

原正文已经要求 group split 后继续检查去重与近重复，但 v3 审计器只比较 `group_id`。这会留下一个可制造错误结论的接口：把同一 raw log、相同内容或已知近重复样本重新编号后，机械检查会把 train/eval 判为无交集。

v4 将身份拆为四层：

1. `group_id`：研究协议选择的 route、scene、episode 或 session 分组；
2. `source_asset_id`：切片和重命名前的原始 log、video 或采集资产；
3. `content_fingerprint`：由冻结规范化流程预先写入的精确内容身份；
4. `similarity_cluster_id`：由离线方法或人工复核预先写入的近重复簇。

审计器要求后三项为非空字符串，并分别拒绝跨 split 交集。注入 fixture 把共享 group 和共享身份放在不同 episode 上；因此三种身份错误可以在不同 `group_id` 下独立触发，而不是对 `group_split_overlap` 的重复计数。

## 可执行证据

- 有效 fixture：0 issue，2 个 episode、6 帧、1 个显式 masked sensor sample；
- 注入 fixture：11 issue / 11 issue types，其中 1 个 group overlap、3 个 identity overlap；
- 第4章单元测试由 14 个增至 18 个，全书由 297 个增至 301 个；
- `check_results.py` 要求脚本输出与 `results/ch04/EXP-04-01-smoke.json` 精确相等。

## 不能外推的结论

- `content_fingerprint` 只覆盖其规范化流程定义的精确身份；转码、裁剪、时移或视角变化可能绕过它；
- `similarity_cluster_id` 是上游检索/人工流程的输出，不是审计器自动发现的事实；
- perceptual hash 或 embedding 阈值会同时产生漏检和误合并，真实实验必须锁定算法、模型 revision、预处理和阈值并抽查边界样本；
- 四层 ID 均无交集仍不是统计独立、场景独立或分布外泛化的充分证据；
- 本阶段没有下载、解码或查看真实机器人/自动驾驶媒体，也没有验证隐私、许可或采集标定。

## 自动驾驶正文影响

正文现在明确指出：同一 raw log 切出的不同文件，即便文件名、episode ID 和 route ID 都不同，仍是直接同源样本。驾驶数据还需继续按 scene/route、城市、日期、车辆和事件语义分组；近重复检索只用于发现协议遗漏，不能替代这些分组。
