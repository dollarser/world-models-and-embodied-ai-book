# 第10章 probe 偏移与动作接口审查

> 审查日期：2026-09-01
> 范围：第10章正文、`EXP-10-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过；官方 checkpoint、真实视频、GPU、因果与规划性能仍未验证

## 1. 发现与修复

原实验只报告纹理相关性反转后的 probe，虽然能展示重建与任务指标排序相反，却没有显示 appearance 捷径在正常分布下会得到高分。读者因而难以理解为何单一 ID probe 不足。v2 fixture 增加未参与拟合的 ID 集：appearance 与 task-predictive 都为 100%，shift 后分别为 0% 和 100%，collapsed 在两者均为 50%。训练、ID 与 shift 样本角色现在显式分离。

正文还正确提醒“probe 好不等于规划正确”，但原先缺少可执行证据。新增八条解析转移，使 action-blind 与 action-conditioned 接口都能零误差读出当前状态；前者反事实转移 RMSE 为 1、动作敏感度为 0，后者为 0 和 2。这验证的是接口非等价，不是学习模型性能、因果发现或规划成功。

## 2. 一手资料复核

- V-JEPA 2 论文与官方仓库均把 V-JEPA 2-AC 描述为从 V-JEPA 2 后训练得到的 latent action-conditioned world model；论文摘要明确为少于 62 小时 DROID 视频。
- V-JEPA 2.1 论文与官方仓库一致列出 dense predictive loss、deep self-supervision、图像/视频 tokenizer 和模型/数据扩展四项组成。
- 官方仓库当前列出 80M 参数、384 分辨率的 ViT-B/16 checkpoint 与 `vjepa2_1_vit_base_384` Hub 入口，也明确提醒默认 `decord` 不支持 macOS。
- 上述信息只支持型号、方法和接口描述；没有下载权重，不能据此声称 24 GB 推理可行。官方多节点预训练配置也不支持本书单卡训练结论。

## 3. 代码与一致性审查

第10章由 5 增至 12 个单元测试，全书由 190 增至 197 个。新测试覆盖 held-out ID/shift 排名、未知 split、畸形 sample、当前状态 readout、反事实转移、动作敏感度、未知接口和非有限输入。实验卡升级为 fixture v2，并登记 `CLAIM-10-06/07`；结果 JSON、正文两张表、manifest 和发布统计逐项同步。

## 4. 保留边界

- 所有数值来自极小的手工标量 fixture，没有置信区间或外部效度；
- 没有运行 I-JEPA、V-JEPA、V-JEPA 2/2.1 或动作条件 checkpoint；
- Docker 只是后续依赖隔离首选，不构成 GPU、解码器或数据许可验证；
- 驾驶表征仍需 route-disjoint、时间扰动、动作干预和闭环评测。
