# EXP-06-01：RSSM 数据流 CPU smoke

## 目的

用标准库程序化系统验证 RSSM 教学所需的数据流和评测边界：

- prior 使用历史状态和动作；
- posterior 使用当前观测修正 prior；
- filtering 与 open-loop rollout 必须分开评测；
- Dreamer 风格的 dynamics/representation KL 前向值相同但梯度目标不同；
- `free_nats` 阈值以下的报告值不能被误读为仍有 KL 梯度；
- CPU smoke 不冒充神经网络训练或论文复现。

## 资源

- 档位：S；
- 数据：运行时生成的一维轨迹；
- 依赖：Python 3.12 标准库；
- GPU：不使用；
- 网络与下载：不需要。

## 运行

优先使用 Docker：

```bash
make ch06-smoke
```

宿主 Python 备用入口：

```bash
make ch06-smoke-local
make ch06-test-local
```

## 输出解释

- `filtering_rmse`：每步获得观测修正后的状态误差；
- `open_loop_rmse`：初始化后不再获得观测的多步 prior 误差；
- `persistence_rmse`：用上一观测预测下一状态的朴素基线。
- `kl_balance`：二分类 prior/posterior 的 raw KL、free-nats 后损失、权重和梯度目标标签。

预期关系只用于 smoke：`open_loop_rmse > filtering_rmse`。该关系不是论文性能主张，也不保证在任意参数和任意随机轨迹上成立。

## 验收边界

通过 smoke 只证明：

1. 命令和数据流可运行；
2. 结果是确定性的；
3. 指标能够区分持续观测修正与 open-loop rollout；
4. 解析算术能够区分 free-nats 阈值两侧，但不冒充自动微分测试。

它不证明模型经过学习，不验证 PlaNet/Dreamer 分数，也不验证 24GB GPU 训练资源。
