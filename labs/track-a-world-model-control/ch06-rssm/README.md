# EXP-06-01：RSSM 数据流 CPU smoke

## 目的

用标准库程序化系统验证 RSSM 教学所需的数据流和评测边界：

- prior 使用历史状态和动作；
- posterior 使用当前观测修正 prior；
- filtering、从 posterior 历史出发的一步 prior 与真正不重置的 open-loop rollout 必须分开评测；
- 改写初始化之后的未来观测不能改变真正 open-loop 的输出；
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
- `posterior_anchored_one_step_prior_rmse`：每步从已吸收历史观测的 posterior 状态预测下一步，仍具有观测可见性；
- `open_loop_rmse`：初始化后不再获得观测的多步 prior 误差；
- `open_loop_absolute_error_by_horizon`：同一条不重置 rollout 在 h1/h4/h8/h16/h31 的绝对误差；
- `persistence_rmse`：用上一观测预测下一状态的朴素基线。
- `future_observation_visibility_audit`：给初始化后的观测统一加1，只允许 filtering/一步 prior 改变，open-loop 必须完全不变。
- `kl_balance`：二分类 prior/posterior 的 raw KL、free-nats 后损失、权重和梯度目标标签。

预期关系只用于 smoke：`filtering_rmse < posterior_anchored_one_step_prior_rmse < open_loop_rmse`，且未来观测偏移不会改变 open-loop。该关系不是论文性能主张，也不保证在任意参数和任意随机轨迹上成立。

## 验收边界

通过 smoke 只证明：

1. 命令和数据流可运行；
2. 结果是确定性的；
3. 指标能够区分持续观测修正、posterior-anchored one-step 与 no-reset open-loop rollout；
4. 解析算术能够区分 free-nats 阈值两侧，但不冒充自动微分测试。

它不证明模型经过学习，不验证 PlaNet/Dreamer 分数，也不验证 24GB GPU 训练资源。
