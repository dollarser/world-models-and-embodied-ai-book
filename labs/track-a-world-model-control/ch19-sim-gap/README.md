# EXP-19-01：仿真偏差校准 smoke

固定动作序列在 nominal 参数和带执行器增益、一步延迟、观测尺度偏差的 target 规则中 rollout。小型网格用独立校准序列恢复参数，再在 held-out 动作上验证；实验同时检查窄/宽 domain-randomization 范围是否覆盖 target。

```bash
make ch19-test-local
make ch19-smoke-local
make ch19-smoke
```

该实验不安装 MuJoCo、MetaDrive、CARLA 或 Isaac Lab，不训练策略，也不证明真实 sim-to-real。它只提供参数、偏差归因、校准/验证分离和覆盖审计接口。代码与 fixture 按仓库 MIT 许可发布。
