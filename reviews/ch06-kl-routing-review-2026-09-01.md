# 第6章 KL 路由与 free-nats 审查

> 审查日期：2026-09-01
> 范围：第6章正文、`EXP-06-01` v2、fixture、测试、结果、实验卡、manifest 与第8章接口
> 结论：RSSM 的前向 KL、梯度路由与 free-nats 常数区已分离；未把解析算术写成神经训练结果

## 1. 发现的问题

旧正文用一个加权 `KL(q‖p)` 概括动力学压力，适合入门但不足以解释当前 DreamerV3 实现。读者可能误以为 dynamics/representation loss 是两个不同的前向距离，也可能把 free-nats 后固定为 1 的日志值误解为仍存在同等大小的 KL 梯度。原实验只覆盖 filtering/open-loop 数据流，无法阻止这两类误读。

## 2. 一手实现核对

- 2026-09-01 的 DreamerV3 官方 `rssm.py` 分别计算 `KL(sg(post)‖prior)` 与 `KL(post‖sg(prior))`；
- 两者前向值相同，stop-gradient 只改变梯度接收方；
- 两项分别经过 `max(loss, free_nats)`，当前默认 `free_nats=1.0`；
- 当前默认配置的 dyn/rep 权重分别是 1.0 与 0.1。

这些是核查日期下 `main` 分支的实现事实，不是 PlaNet、DreamerV1/V2 或所有 RSSM 的统一定义。对应一手文件是：

- <https://github.com/danijar/dreamerv3/blob/main/dreamerv3/rssm.py>
- <https://github.com/danijar/dreamerv3/blob/main/dreamerv3/configs.yaml>
- <https://arxiv.org/abs/2301.04104>

## 3. 代码与教学修复

- 新增严格 categorical `KL(posterior‖prior)`，拒绝未归一化、维数不匹配、零/负、布尔及非有限概率；
- 新增 `kl_balance_diagnostic`，同时报告 raw KL、free-nats 后数值、权重、总值和两条梯度目标标签；
- 小失配 raw KL 约 0.005，进入 `free_nats=1` 的常数区；大失配约 1.614，越过阈值；
- 明确标准库 fixture 不运行自动微分，梯度目标是根据已核验实现写入的合同标签，不是测量结果；
- 为 gain、steps、seed 和 RMSE 增加布尔值、类型及有限性拒绝路径。

## 4. 边界与验收

第6章由 3 增至 9 个单元测试，全书由 172 增至 178 个。原 32 步 rollout 指标不变；结果 JSON 改为 `rollout` 与 `kl_balance` 两个命名空间，防止协议指标和训练目标诊断混为一谈。

fixture 没有编码器、解码器、离散 latent、自动微分、优化器、图像、环境、策略、GPU 或车辆。它只验证确定性前向算术和输入合同，不能证明 KL balancing 改善训练，也不能估算 DreamerV3 性能或资源。

阶段门禁包括 22 章 Docker smoke、22 组结果精确比对、4 个 Schema、18 个契约测试、22 张实验卡、3 张 benchmark card、严格文档构建和本地站点检查。
