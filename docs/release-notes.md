# v0.1.0-rc1 发布候选说明

> 冻结日期：2026-08-31
> 本地预览复核日期：2026-09-02
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

这些命令验证共 308 个章节单元测试、61 项严格规格测试、标准库 fixture、输入合同、22 组 smoke—结果 JSON 精确一致性、22 个实验资产包、实验卡/benchmark card/manifest Schema、当前正文显式 EXP/BENCH 版本同步、PRD 的 22 组 S 档—实验卡映射、源码链接、导航、严格站点构建和生成站点内部资源。180 条声明按类型分别治理：26 条 `fact`、8 条 `inference` 和 91 条 `result` 有机器合同；GitHub `official_asset` 事实锚点必须锁完整 commit，研究雷达的 GitHub 官方仓库也必须让 URL 与 revision 指向同一 SHA。55 条 `recommendation` 中 24 条高后果建议另行登记适用条件、动作、替代/停止路径与未授权事项。当前站点还提供面向读者的可检索术语表，以及 12 张按来源版本、资产开放度、复现状态、资源与范围边界登记的研究雷达活页卡。每章都完成内容、代码、一致性和教学审查，机器可读状态为 `reviewed`。第1章用比例反馈、两步观测时延和动作限幅的四组固定对照，把“有反馈”与“有闭环保证”分开；第2章除三态能力矩阵外，还用等权 state-aliasing 对照把 current observation、history cue、任务相关 state 与 decision regret 连起来；第3章显式区分 z-depth/range，验证 optical→body→world 变换链、proper rotation、单位轴与正逆外参，并用解析时间夹具量化过期位姿造成的空间错位；第4章把切分身份拆为 group、raw source、精确内容与预登记近重复簇，证明不同 `group_id` 不足以排除同源或已知重复；第4、8、20章进一步贯通 `terminated/truncated`、value bootstrap 与评测分母：有效 timeout 不再被误删，技术无效运行不能静默进入或离开聚合；同一步双真时保留两种结束原因，并由自然终止关闭 bootstrap；第8章还用累计 survival weight 阻止终止后的伪状态继续贡献 actor/critic loss。第5章用三成员 correlated-error 负对照证明低 disagreement 不蕴含正确，并把 estimator 盲区贯通第9、21章；第6章区分 RSSM 的前向 KL、stop-gradient 路由与 free-nats 常数区，第7章补入随机 rollout 的粒子/ensemble 身份与均值—经验下尾—chance constraint 排序反例，并用固定动作预算把环境 reward、terminal-value contribution 和 planning objective 分账，第9章显式报告长时 rollout 的 attempted/available/coverage 与缺失语义，第10章用 ID/shift probe 暴露捷径，并把状态可读性与动作条件转移分开，第11章再用左右标签交换证明动作敏感不等于方向正确，并固定多步轨迹分母，第12章加入半开米制栅格的 floor/截断负边界，区分 current estimation、future forecasting、action-conditioned world model 与 4D scene generation，并把动态清空证据、观测过期、稀疏 waypoint 路径段和 footprint 扫掠纳入三态路径合同，第13章区分预测/执行时域与时间集成，第14章显式计算候选—batch forward 预算并把模式有效与场景安全筛选分开，第15章阻止动作包扩大执行时域并拒绝 replay、乱序、错误 clock 和字段顺序，第16章用 schema fingerprint 约束 raw adapter 与统计量版本身份，并拆开四种动作统一路线，第17章把代理评测拆成动作注入、rollout 与 outcome scorer 三段误差，并用两套 authored support 声明证明 gate 能阻断 coverage 外 model exploitation、不能验证 coverage 内预测，第18章用联合轨迹门禁暴露 marginal support 假阳性，并验证全同 reward group 的 leave-one-out advantage 退化，第19章修复 gain×scale 结构混淆，区分 observation 拟合、隐藏 state 与 state-anchor 可辨识性，第20章把手工协议 smoke 从 E4 更正为 E0，用 2×2 格揭示任务总体与成功规则的交互，并用配对 route 反例区分 episode-micro、cluster-macro 与 cluster bootstrap，避免把 warning、重复运行或区间含零误读为因果贡献或等效证据；第21章加入 deadline burst、异步 chunk stale/underflow、fallback 升级恢复、健康/完成/授权分离、fallback 生命周期锁定和绑定及时效化 receipt，避免用非空队列、恢复健康、未完成授权或可重放布尔值代替运行时安全证据；第22章除五段证据 trace 外，还用 artifact digest/producer/claim binding、冻结独立评测、三分区 × 四身份维度数据隔离和结构化 safety gateway 阻止“有文件名或布尔标记即完成”的弱证据。

在线自学出口已覆盖 22 章共 116 道练习：每题具有折叠式同编号自检要点，并由 manifest 与机器门禁保证题目—答案双向对应、顺序一致、标签闭合且不是空壳内容。自检给出最低合格证据链，不把开放题收窄为唯一答案，也不把纸面推理冒充实验复现。

## 没有验证什么

本候选没有训练 Dreamer、VLA、diffusion policy、occupancy 或 learned simulator，没有下载大型数据/checkpoint，没有运行 GPU、MetaDrive、CARLA、MuJoCo、Isaac、ROS、机器人或车辆。正文引用的论文/项目结果不是本书实测；S 档结果只验证教学合同、反例和追溯路径。

因此，本候选不提供模型性能、24 GB 可复现性、实时性、安全认证或道路部署保证。带 M/L1/L2 的章节保留 `gpu_status: pending`，不会仅因站点发布而升级为 `reproducible`。

## 已知限制与后续升级

- 外部链接和快速演进案例需要按资料核查日期周期性复核；
- 已用回环静态服务器打开严格编译产物的应用内浏览器面板，并自动检查 29 个 HTML、22 章页面和 1161 个内部目标；截图式多尺寸与可访问性巡检仍需在发布操作中人工确认；
- 后续有合法数据和算力时，应按实验卡逐项执行 M/L1/L2，而不是批量补写未经运行的结果；
- 任一目标硬件实验失败都应保留失败记录并缩小声明，不影响本 CPU 证据版本的可读性。
