# 第17章双用途世界模型审查

> 审查日期：2026-09-02
> 范围：第17章 simulator/policy 双用途证据设计、A2World 一手来源、开放资产与资源边界
> 结论：通过；论文架构、开放资产与两条能力验收已分层，完整门禁通过

## 发现

原章把世界模型帮助策略拆成五种非互斥用途，并明确代理评测的动作注入、rollout 与 outcome scorer 三段误差，分类是合理的。但它缺少一个当代案例来回答更容易混淆的问题：同一预训练动力学先验若同时用于 simulator 和 policy，是否可以共享完成标准。没有具体资产边界时，读者容易把“共享权重”误读为两种能力已被同一指标验证。

## 修改与证据

- [ECCV 2026 官方收录页](https://eccv.ecva.net/virtual/2026/poster/3656)用于确认论文接收状态 `[P]`，[`arXiv:2606.29501v1`](https://arxiv.org/abs/2606.29501v1)用于核对 action-to-video 先验、A2World-sim 与 A2World-policy 的论文架构；
- [官方仓库快照 `077e10a`](https://github.com/LogosRoboticsGroup/A2World/tree/077e10ad6cee07342b5e779f11fea78247584834)用于核对当前 code release 聚焦 world-model/A2World-sim，而不是把论文中的 policy 分支误报为已发布代码；
- 将验收拆成先验消融、simulator 分支、policy 分支和共享收益四组证据，明确生成视频质量不能替代 policy 闭环结果，单分支获益也不能证明另一分支获益；
- 新增 `CLAIM-17-09` 并登记到 manifest、`fact-evidence.json` 和研究雷达，事实只覆盖论文架构与已发布资产范围；
- 区分仓库 Apache-2.0 源码、NVIDIA Cosmos 衍生 checkpoint 条款、外部基础资产和上游 `GPUS=8` 全量微调示例。

## 证据边界

本阶段只做一手论文、官方会议页面和锁定仓库的零下载审计。没有下载模型、checkpoint 或数据，没有安装上游环境，没有运行 GPU、仿真、机器人或车辆，也没有证明 24 GB 单卡或 2×80 GB 路径。`[P/O,R1]` 表示正式收录与部分开放资产已经核对，不表示论文指标、simulator fidelity 或 policy performance 已由本书复现。

## 门禁结果

- `make smoke-all`：通过，22 章共 308 个单元测试，22 组 smoke 均与登记结果一致；
- `make docs-preview-check`：通过，29 个 HTML、22 章、23 张可访问 Mermaid 图、116 个折叠式自检和 1161 个内部目标，附带 3 项生成站点语义测试；
- `make check`：通过，4 个 Schema、22 章、22 张实验卡、3 张 benchmark card 与 63 项严格规格测试通过；
- `git diff --check`：通过。
