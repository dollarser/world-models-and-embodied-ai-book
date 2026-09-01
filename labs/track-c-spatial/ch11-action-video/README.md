# EXP-11-01：动作条件、错位标签与多步 rollout smoke

该实验从单步转移样本学习动作—位移表，再将状态渲染成 ASCII 帧。测试集只包含训练时未出现的动作序列，并比较：

- `action_blind`：忽略动作，只使用平均转移；
- `left_right_swapped`：响应动作，但交换左右控制语义；
- `action_conditioned`：根据 forward/left/right/brake 预测不同未来。

`action_sensitivity` 统一为同一状态下预测未来的最大两两欧氏距离，完全忽略动作必须为 0。交换模型与正确模型的敏感度和无符号左右分离都为 2，但有符号左右效果分别为 -2 和 +2，因此“有响应”不等于“方向正确”。多步结果显式登记 3 条序列、9 个转移以及全轨迹 RMSE，避免只看可能被误差抵消的终点。

```bash
make ch11-test-local
make ch11-smoke-local
make ch11-smoke
```

它验证动作敏感性、方向/幅度正确性和固定分母多步 rollout 协议，不是视频生成、因果发现或驾驶模型。代码与程序化 fixture 按仓库 MIT 许可发布。
