# 第6章 benchmark KL 合同一致性审查

> 日期：2026-09-02
> 范围：`BENCH-06-01`、`EXP-06-01` v2、`CLAIM-06-02/03/05/06`
> 结论：关闭正文与实验已扩展到 KL v2、benchmark 仍停留在 rollout v1 的协议漂移；不升级神经训练或梯度证据

## 1. 发现的问题

第6章正文、`experiment-card.json`、源码与中央结果已经包含两组 categorical KL、stop-gradient 目标标签和 free-nats 阈值算术；但 `BENCH-06-01` 仍只登记最初的31个转移与三个 RMSE，claim IDs 只有 `CLAIM-06-02/03`，协议版本和实现版本仍为 v1。

现有 Schema 能证明 benchmark card 结构合法，却不能自动判断后来新增的章节主张是否仍由该 benchmark 覆盖。因此旧卡不是错误数据，但已经不能完整描述当前 `EXP-06-01` 的评测合同。

## 2. 官方实现复核

重新核对 DreamerV3 官方 commit `e3f02248693a79dc8b0ebd62c93683888ddaccfe`：

- [`rssm.py`](https://github.com/danijar/dreamerv3/blob/e3f02248693a79dc8b0ebd62c93683888ddaccfe/dreamerv3/rssm.py) 使用 `KL(sg(post) || prior)` 与 `KL(post || sg(prior))`，并分别取 `max(loss, free_nats)`；
- [`configs.yaml`](https://github.com/danijar/dreamerv3/blob/e3f02248693a79dc8b0ebd62c93683888ddaccfe/dreamerv3/configs.yaml) 在被审查配置中给出 `free_nats=1.0` 与 dyn/rep scale=`1.0/0.1`。

这与正文和当前解析 fixture 一致。它只证明锁定源码快照的实现事实，不代表所有 Dreamer/RSSM 或未来 commit。

## 3. 修复内容

`BENCH-06-01` 升级为 v2：

- claim coverage 加入 `CLAIM-06-05/06`；
- 增加 `categorical_kl_route_audit` 系统与两行概率 fixture；
- `sample_count` 从31变为33，明确31个转移与2个 KL case 是不同分析单元；
- 冻结 posterior/prior、KL 方向、threshold、scale 与禁止声明；
- 新增 `METRIC-06-04/05/06`，分别登记 raw KL、free-nats-clamped forward KL 与 weighted total；
- 把 gradient target 保留为源码派生的合同标签，不冒充自动微分测量；
- 更新第6章、第9章 benchmark 概览、PRD、状态和发布说明。

## 4. 证据边界

- 两个 KL case 是作者构造的二分类分布，不是 learned latent；
- 前向 dyn/rep 数值相同不证明实际梯度大小相同，只说明 stop-gradient 不改变被代入的概率值；
- 标准库没有 autodiff graph，不能验证 encoder/prior 参数梯度、posterior collapse、收敛或优化稳定性；
- `free_nats=1.0` 与 scale=`1.0/0.1` 是具名 commit 配置，不是通用推荐；
- 没有下载权重、数据，没有运行 GPU、Dreamer 或神经 RSSM。

## 5. 验证

- `make check-local`：通过；
- `make smoke-all`：通过，全书333项章节测试；
- `make docs-preview-check`：通过，29个HTML、22章、23张可访问 Mermaid、121个折叠自检和1161个内部目标；
- `make check`：通过，4个 Schema、22章、22张实验卡、3张 benchmark card 与67项严格规格测试；
- `git diff --check`：通过。
