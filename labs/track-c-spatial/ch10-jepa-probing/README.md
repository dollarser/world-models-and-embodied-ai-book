# EXP-10-01：表征指标排序反转 smoke

该实验构造三个手工表征：保留高能量纹理的 `appearance`、保留任务变量的 `task_predictive` 和完全坍塌的 `collapsed`。训练集的纹理与任务同向，测试集反向，因此：

- `appearance` 的重建误差更低，但 shifted probe 失败；
- `task_predictive` 无法重建纹理，却保留任务变量；
- `collapsed` 用作 probe 实现的负对照。

```bash
make ch10-test-local
make ch10-smoke-local
make ch10-smoke
```

该 fixture 不加载 V-JEPA、I-JEPA 或任何官方 checkpoint，不代表模型性能。代码和程序化数据按仓库 MIT 许可发布。
