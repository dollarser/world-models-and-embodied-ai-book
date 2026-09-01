# v0.1.0-rc1 发布候选说明

> 冻结日期：2026-08-31
> 本地预览复核日期：2026-09-01
> 发布形态：在线书候选，不计划纸质出版
> 许可证：仓库原创正文、代码、图表与 fixture 使用 MIT；第三方资产遵循各自条款

## 本候选包含什么

- 7 个部分、22 章中文正文，面向有计算机视觉基础但无 3D、机器人学或强化学习经验的读者；
- 22 张实验卡、3 张代表性 benchmark card、22 组零下载或微型 CPU fixture、结构化结果与 Docker smoke；
- world model、空间表征、模仿/生成策略、VLA、策略融合、仿真、评测、部署安全与综合项目；
- 自动驾驶贯穿正文，MetaDrive 是后续驾驶 M 档默认闭环环境，CARLA 是高保真可选扩展；
- 默认训练资源目标不超过 24 GB 单卡，最高可选路径不超过 2×80 GB，且购置硬件不是必需条件。

## 已验证范围

发布候选门禁为：

```bash
make smoke-all
make check
make docs-build
make docs-preview-check
git diff --check
```

这些命令验证共 246 个章节单元测试、标准库 fixture、输入合同、22 组 smoke—结果 JSON 精确一致性、实验卡/benchmark card/manifest Schema、源码链接、导航、严格站点构建和生成站点内部资源。当前站点还提供面向读者的可检索术语表。每章都完成内容、代码、一致性和教学审查，机器可读状态为 `reviewed`。第2章用三态能力矩阵阻止从系统名称推断转移、动作干预或规划能力；第3章显式区分 z-depth/range 并验证 optical→body 单位轴与正逆外参；第4、8、20章进一步贯通 `terminated/truncated`、value bootstrap 与评测分母：有效 timeout 不再被误删，技术无效运行不能静默进入或离开聚合；同一步双真时保留两种结束原因，并由自然终止关闭 bootstrap。第6章区分 RSSM 的前向 KL、stop-gradient 路由与 free-nats 常数区，第9章显式报告长时 rollout 的 attempted/available/coverage 与缺失语义，第10章用 ID/shift 对照暴露 probe 捷径，并把状态可读性与动作条件转移分开，第11章再用左右标签交换证明动作敏感不等于方向正确，并固定多步轨迹分母，第12章把动态清空证据、观测过期和 footprint 扫掠纳入三态路径合同，第13章区分预测/执行时域与时间集成，第14章显式计算候选—batch forward 预算并把模式有效与场景安全筛选分开，第15章阻止动作包扩大执行时域并拒绝 replay、乱序、错误 clock 和字段顺序，第16章用 schema fingerprint 约束 raw adapter 与统计量版本身份，并拆开四种动作统一路线，第17章把代理评测拆成动作注入、rollout 与 outcome scorer 三段误差，并用 support gate 对照阻断 support 外 model exploitation，第18章用联合轨迹门禁暴露 marginal support 假阳性，并验证全同 reward group 的 leave-one-out advantage 退化，第19章修复 gain×scale 结构混淆，区分 observation 拟合、隐藏 state 与 state-anchor 可辨识性，第20章把手工协议 smoke 从 E4 更正为 E0，并用 2×2 格揭示任务总体与成功规则的交互，避免把 warning 当作可加因果贡献；第21章加入 deadline burst、异步 chunk stale/underflow 与 fallback 升级恢复合同，避免用非空队列或单次降级标签代替运行时安全证据；第22章用五段证据 trace 把输入、方法、独立评测、安全门和交付包连接成机器可审计依赖图。

## 没有验证什么

本候选没有训练 Dreamer、VLA、diffusion policy、occupancy 或 learned simulator，没有下载大型数据/checkpoint，没有运行 GPU、MetaDrive、CARLA、MuJoCo、Isaac、ROS、机器人或车辆。正文引用的论文/项目结果不是本书实测；S 档结果只验证教学合同、反例和追溯路径。

因此，本候选不提供模型性能、24 GB 可复现性、实时性、安全认证或道路部署保证。带 M/L1/L2 的章节保留 `gpu_status: pending`，不会仅因站点发布而升级为 `reproducible`。

## 已知限制与后续升级

- 外部链接和快速演进案例需要按资料核查日期周期性复核；
- 已用回环静态服务器打开严格编译产物的应用内浏览器面板，并自动检查 27 个 HTML、22 章页面和 986 个内部目标；截图式多尺寸与可访问性巡检仍需在发布操作中人工确认；
- 后续有合法数据和算力时，应按实验卡逐项执行 M/L1/L2，而不是批量补写未经运行的结果；
- 任一目标硬件实验失败都应保留失败记录并缩小声明，不影响本 CPU 证据版本的可读性。
