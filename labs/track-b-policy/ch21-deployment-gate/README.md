# EXP-21-01：deadline 与部署安全网关 smoke

固定 6 个延迟样本说明均值通过不代表每个控制周期满足 deadline；固定动作 packet 分别注入旧观测、超时、非有限动作、越界动作和过期 action chunk。

```bash
make ch21-test-local
make ch21-smoke-local
make ch21-smoke
```

该实验不运行模型、网络、ROS、机器人、车辆或 GPU，也不是实时系统或安全认证。fallback 标签只演示按本体/运行设计域配置的接口，不证明具体动作安全。代码与 fixture 按仓库 MIT 许可发布。
