# EXP-19-01：仿真偏差校准 smoke

固定动作序列在 nominal 参数和带执行器增益、一步延迟、观测尺度偏差的 target 规则中 rollout。observation-only 网格校准会发现两个零误差参数解：不同 gain/scale 乘积相同，即使换 held-out 动作仍无法区分；加入独立 state anchor 后才得到唯一网格解。另一组载荷 fixture 证明重复同一工况仍保留三个 `force_gain/base_load` 等价解，加入第二个不同且已知的载荷后才在当前网格中收缩为一个。实验同时检查窄/宽 domain-randomization 范围是否覆盖 target。

```bash
make ch19-test-local
make ch19-smoke-local
make ch19-smoke
```

该实验不安装 MuJoCo、MetaDrive、CARLA 或 Isaac Lab，不训练策略，也不证明真实 sim-to-real。它只提供参数可辨识性、偏差归因、校准/验证分离、工况信息增量和边界覆盖审计接口；唯一解来自无噪目标恰在手工网格，不能外推到连续、带噪或接触系统。代码与 fixture 按仓库 MIT 许可发布。
