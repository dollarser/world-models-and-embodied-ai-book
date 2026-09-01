# EXP-15-01：VLA 动作合同与执行网关 smoke

fixture 将连续回归、离散 action token 和 flow action chunk 解码为同一个移动底盘动作 schema，并验证 frame、字段顺序、单位、共同 clock、墙钟时间戳、观测/首动作 timestep、边界、command ID 与 prediction/execution horizon。高层文本、过期命令、合同错配、越界动作、执行时域越权、replay、乱序，以及墙钟新鲜但 step 错位的 packet 必须被拒绝。

```bash
make ch15-test-local
make ch15-smoke-local
make ch15-smoke
```

它不运行 VLA、VLM API、机器人或仿真器。固定 timestep 只验证一个手工调度槽；单调 command ID 只覆盖单会话顺序，不提供时钟同步、认证、防篡改或跨重启持久性，也不证明动作安全。代码和 fixture 按仓库 MIT 许可发布。
