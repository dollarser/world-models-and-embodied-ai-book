# EXP-15-01：VLA 动作合同与执行网关 smoke

fixture 将连续回归、离散 action token 和 flow action chunk 解码为同一个移动底盘动作 schema，并验证 frame、字段顺序、单位、共同 clock、时间戳、边界、command ID 与 prediction/execution horizon。高层文本、过期命令、合同错配、越界动作、执行时域越权、replay 和乱序必须被拒绝。

```bash
make ch15-test-local
make ch15-smoke-local
make ch15-smoke
```

它不运行 VLA、VLM API、机器人或仿真器。单调 command ID 只覆盖单会话顺序，不提供认证、防篡改或跨重启持久性，也不证明动作安全；这里只验证模型输出到低层控制器之间的契约。代码和 fixture 按仓库 MIT 许可发布。
