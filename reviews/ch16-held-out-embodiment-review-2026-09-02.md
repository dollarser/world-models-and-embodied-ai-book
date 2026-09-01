# 第16章 held-out-embodiment 协议审查

> 审查日期：2026-09-02
> 范围：第16章跨本体迁移协议、XEWorld v1 一手来源、声明与证据登记
> 结论：通过；协议事实与作者结果已分层，完整门禁通过

## 发现

原章已要求 leave-one-embodiment-out、区分 seen/few-shot/zero-shot，并建议用迁移矩阵报告正负迁移，方向合理。但“留出一个数据集或机器人名称”仍可能同时改变场景、相机、物体和任务；原协议也没有要求把视觉、形态、运动学和物体动力学分开归因，或在 few-shot 后同时检查目标收益与已见本体遗忘。

## 修改与证据

- 以 [XEWorld `arXiv:2608.05799v1`](https://arxiv.org/html/2608.05799v1) 为一手来源，加入五种双臂机器人、25 个任务、三训练/二留出和 leave-one-embodiment-out 的协议案例；
- 要求相同 task/seed 下固定场景布局、物体位姿、光照和相机，并把不可固定的物理差异显式记录；
- 分开报告视觉质量、机器人形态、运动学和物体动力学，避免单一聚合分数掩盖失败归因；
- 把 pixel-space action、时间对齐 cue 和 few-shot forgetting 写为论文作者在所测模型上的结果，不写成本书实测或普遍定理；
- 新增 `CLAIM-16-08` 事实声明并登记到 manifest 与 `fact-evidence.json`，研究雷达从正文候选升级为已纳入案例卡。

## 证据边界

本阶段没有下载代码、数据、模型或 checkpoint，没有运行 GPU、仿真或真实机器人，也没有复现论文数值。`[A,R0]` 表示已经审计 arXiv 一手论文，但本书复现状态仍为 R0。协议可用于改进实验设计，不能借此声称论文作者结论已经独立验证。

## 门禁结果

- `make smoke-all`：通过，22 章共 308 个单元测试，22 组 smoke 均与登记结果一致；
- `make docs-preview-check`：通过，29 个 HTML、22 章、23 张可访问 Mermaid 图、116 个折叠式自检和 1161 个内部目标，附带 3 项生成站点语义测试；
- `make check`：通过，4 个 Schema、22 章、22 张实验卡、3 张 benchmark card 与 61 项严格规格测试通过；
- `git diff --check`：通过。
