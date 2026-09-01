# 第9章长时分母与动作干预审查

> 审查日期：2026-09-01
> 范围：第9章正文、`BENCH-09-01` v2、`EXP-09-01` v2、fixture、测试、结果、实验卡、manifest 与第20/21章接口
> 结论：逐 horizon 分母、缺失语义和 E2 action sensitivity 已进入可执行证据；未把手工惩罚写成自然误差或真实崩溃率

## 1. 发现的问题

正文已要求误差曲线同时报告每个 horizon 的有效样本数，但旧 fixture 只有 one-step RMSE 与两个闭环 episode，没有验证该要求。若视频生成中断、latent 非有限或解码失败的 rollout 被直接删除，长 horizon 均值会条件于幸存样本，甚至让更脆弱的模型看起来更好。旧实验也只用单元测试判断 action-blind，没有在结果中登记 E2 action sensitivity。

## 2. 一手资料核对

- 2026 年 decision-making-centric 立场论文把长时 rollout、干预、policy-induced shift、model exploitability 和 uncertainty calibration 明确列为决策用途证据；
- WorldArena 官方仓库分别提供感知质量、合成数据、策略评估和动作规划等功能评测，并同时提供综合 EWMScore；
- WorldArena 2.0 又按 modality、functionality 和 platform 扩展评测对象；
- KineBench 指出 inverse dynamics model 会引入端到端归因混淆，并用显式运动学落地减少该混淆。

正文保留“分项证据不能被综合分数抹平”的边界，没有运行或抄录排行榜。对应一手来源：

- <https://arxiv.org/abs/2606.15032>
- <https://github.com/tsinghua-fib-lab/WorldArena>
- <https://arxiv.org/abs/2605.17912>
- <https://arxiv.org/abs/2607.19876>

## 3. 代码与教学修复

- `action_sensitivity` 报告同一状态三个候选动作预测值的极差：action-blind 为 0，action-faithful 为 0.2；
- `horizon_error_report` 保留 attempted count、available count、coverage、available-case mean 和固定分母 mean；
- 缺失必须是 rollout 后缀，不能在缺失后重新出现有效值；所有误差、惩罚、状态、目标和步数都有类型、有限性及范围拒绝路径；
- stable/fragile 各三条 rollout：第4步 available-case 选择 fragile（0.4 对 0.8），预注册缺失惩罚 2.0 后固定分母选择 stable（1.4667 对 0.8）；
- 结果明确把惩罚 2.0 标为本 fixture 的协议常数，不是经验校准误差、安全成本或通用推荐。

## 4. 边界与验收

第9章由 3 增至 9 个单元测试，全书由 178 增至 184 个。`BENCH-09-01` 升为 v2，冻结 E1/E2/E4、4/24 步 horizon、六条误差行、缺失惩罚、动作集合和失败定义。

fixture 没有图像、learned world model、随机任务、自然 missingness、uncertainty estimator、置信区间、仿真器、机器人、车辆或 GPU。排序反转只证明分母语义会影响结论；真实 benchmark 必须先定义技术无效、任务失败或幸存条件 estimand，再选择相应处理。

阶段门禁包括 22 章 Docker smoke、22 组结果精确比对、4 个 Schema、18 个契约测试、22 张实验卡、3 张 benchmark card、严格文档构建和本地站点检查。
