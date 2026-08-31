# EXP-11-01：动作条件 counterfactual smoke

该实验从单步转移样本学习动作—位移表，再将状态渲染成 ASCII 帧。测试集只包含训练时未出现的动作序列，并比较：

- `action_blind`：忽略动作，只使用平均转移；
- `action_conditioned`：根据 forward/left/right/brake 预测不同未来。

```bash
make ch11-test-local
make ch11-smoke-local
make ch11-smoke
```

它验证动作敏感性、counterfactual 分离和多步 rollout 协议，不是视频生成或驾驶模型。代码与程序化 fixture 按仓库 MIT 许可发布。
