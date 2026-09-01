# 当前读者文档 GitHub 来源快照审查

> 审查日期：2026-09-02
> 范围：`docs/**/*.md` 中具体 GitHub 文件/目录实现来源
> 涉及章节：第4、13、14、15、17、18、19、21章
> 结论：通过；14 个浮动实现链接已清零，语义修正、回归门禁与完整门禁均已完成

## 审查方法

先枚举当前读者文档中的 `blob/main`、`tree/main`、`blob/master` 和 `tree/master`，再用官方仓库 HEAD 取得完整 commit，逐一确认目标文件在该 revision 返回成功，并阅读支持正文结论的源码或文档段落。仓库首页可以保留为发现入口，但不能支撑带“当前实现”含义的版本化声明。

## 锁定快照

- LeRobot `128d3324e3202ce1fca1340fb8d7941edecce9d3`：Dataset 时间窗口、Diffusion Policy 配置、异步 server、sync/RTC 与 async 指南；
- ACT `742c753c0d4a5d87076c8f69e5628c79a8cc5488`：`m=0.01` temporal aggregation；
- Isaac-GR00T `51d4c89f72fda44cbf77285c6a8114b52676b8a1`：N1.7 README 与 16 步数据窗口示例；
- Cosmos-Predict2.5 `a2c298b0a3df3778b973fe65e9e58877b292d8a7`：action-conditioned 指南与默认 state→relative-action loader；
- Cosmos 3 `9aa98e5a0773a5558f07d2699e640858f7ca8827`：forward/inverse/policy action cookbook；
- RIPT-VLA `440990e8864e12e4578b490ff6359e4f2c49ae3e`：RLOO/dynamic sampling/PPO 训练入口；
- MuJoCo `005b35170d16cf20d1eb5afcecf67328e6ec0875`：System Identification Toolbox；
- Autoware Universe `af47e1e26cfb40240439f3876fee0356bb4a1c75`：operation-mode transition manager。

## 内容准确性修正

- 第15章不再含糊地说异步 server “附加 observation 起点”，而是按实现说明从 observation 时间戳/timestep 构造每个动作的执行时间与步号；
- GR00T 的 Apache-2.0 只描述代码仓库，checkpoint 访问和模型许可要求单独核对；
- 第17章分别引用 Cosmos 2.5 的公开指南和实际默认 loader，避免用指南链接间接支撑源码行为；
- 第18章把 `train_ript.py` 能直接支持的范围收窄为 QueST + LIBERO，不再由单个入口文件推断 OpenVLA-OFT 已接入。

锁定快照只证明“本次审查了什么”，不证明上游代码已由本书运行，也不验证模型效果、GPU 资源、真实机器人、车辆或安全性能。

## 自动门禁

`check_floating_github_source_contract` 扫描当前 `docs/**/*.md` 并拒绝四类浮动分支链接。两项单元测试覆盖 main/master 反例、完整 commit 正例，以及非 GitHub/仓库落地页边界。

## 门禁结果

- `make smoke-all`：通过，22 章共 308 个单元测试，22 组 smoke 与登记结果精确一致；
- `make docs-preview-check`：通过，29 个 HTML、22 章、23 张可访问 Mermaid 图、116 个折叠式自检、1161 个内部目标与 3 项生成站点语义测试通过；
- `make check`：通过，4 个 Schema、22 章、22 张实验卡、3 张 benchmark card 与 63 项严格规格测试通过；
- `git diff --check`：通过。
