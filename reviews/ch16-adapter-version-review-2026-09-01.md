# 第16章跨本体 adapter 版本身份审查

> 审查日期：2026-09-01
> 范围：第16章正文、`EXP-16-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过 S 档内容、代码、一致性和教学审查；不升级 GPU 或真实迁移状态

## 发现与修复

旧 fixture 能拒绝缺失 `embodiment_id`，但一条历史记录会无条件使用注册表中的当前 adapter。若单位、scale、夹爪极性或字段顺序后来改变，同一 raw tensor 可能被静默解释成新语义。round-trip 只证明当前 adapter 对当前四条样本可逆，不能发现这种版本漂移。

本轮为记录加入确定性 adapter schema fingerprint，输入包含本体 ID、raw 字段顺序、单位、scale、夹爪极性和 canonical schema 版本。缺失本体、缺失 fingerprint 和陈旧 fingerprint 三类错误均在 canonicalize 前拒绝；语义配置变化必须改变 fingerprint。该机制只提供缓存/版本身份，不是认证、签名、数据真实性或控制器安全机制。

## 内容核验

- 用 Octo 官方数据管线说明 pad/mask、dataset identity 与物理语义统一不是同一件事；
- 用 Isaac-GR00T 当前统计量实现核验 schema fingerprint 的工程动机，并补充 action representation、delta indices 与 stats 必须共同版本化；
- 用 openpi 与 LeRobot 官方 normalization 文档说明 checkpoint stats、dataset stats 和 override 是模型—数据—动作合同，不是可随意替换的数值文件；
- 明确区分训练 mixture 已见目标本体、少量目标数据适配和完全未见本体 zero-shot，避免把三类结果统称“跨本体泛化”；
- learned tokenizer 只统一表示；仍需本体 decoder、重建与闭环可执行性证据。

## 固定结果

- 12 个章节单元测试通过；
- naive raw pooling canonical MAE 为 `0.28375`；schema-aware pooling 为 `0`；
- 四条记录最大 adapter round-trip 误差为 `0`；
- 三类错误记录拒绝率为 `3/3`；
- 修改 `arm_a` scale 或字段合同会改变 SHA-256 fingerprint。

## 证据边界

没有下载 Open X-Embodiment、DROID 或 checkpoint，没有训练策略、learned adapter/tokenizer，没有运行 GPU、仿真、机器人或车辆。两维手工 fixture 不是正/负迁移、zero-shot、本体泛化、性能、安全或防篡改证据。
