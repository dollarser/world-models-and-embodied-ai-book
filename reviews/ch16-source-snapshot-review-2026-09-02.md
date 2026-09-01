# 第16章实现级来源快照审查

> 审查日期：2026-09-02
> 范围：第16章 Octo、Isaac-GR00T、openpi、LeRobot 与 OpenVLA-OFT 实现级说明
> 结论：通过；来源路径、实现语义与完整门禁均已复核

## 发现

第16章已有来源链接可以支撑正文方向，但五项实现级引用仍指向 `main` 或仓库首页。上游更新后，同一链接可能不再对应本次审查的实现。进一步读取 GR00T 源码还发现，原文“relative/absolute 表示”范围过宽：当前 fingerprint 逻辑明确绑定 relative-action 统计缓存，不足以证明所有 absolute-action 统计路径都受相同合同保护。

## 修改与固定证据

- Octo `241fb3514b7c40957a86d869fecb7c7fc353f540`：确认 pad、action normalization mask 与 dataset name；
- Isaac-GR00T `51d4c89f72fda44cbf77285c6a8114b52676b8a1`：确认 relative-action fingerprint 包含 embodiment、rep/type、format、action/state delta indices 与 state key；
- openpi `215abfb217dbac7d5f1273282331b9b1866c0479`：确认预训练 action-space 条件，以及复用/重算 normalization stats 的比较建议；
- LeRobot `128d3324e3202ce1fca1340fb8d7941edecce9d3`：确认 checkpoint、dataset 与显式 stats override 路径；
- OpenVLA-OFT `e4287e94541f459edc4feabc4e181f537cd569a8`：确认 README 所列约 16–18 GB 推理与 27–80 GB 训练资源范围。

这些快照只固定本次阅读的源码和 README，不表示代码已执行、资源声明已在本书硬件实测，也不把官方实现升级为独立复现。

## 门禁结果

- `make smoke-all`：通过，22 章共 308 个单元测试，22 组 smoke 与登记结果精确一致；
- `make docs-preview-check`：通过，29 个 HTML、22 章、23 张可访问 Mermaid 图、116 个折叠式自检、1161 个内部目标与 3 项生成站点语义测试通过；
- `make check`：通过，4 个 Schema、22 章、22 张实验卡、3 张 benchmark card 与 61 项严格规格测试通过；
- `git diff --check`：通过。
