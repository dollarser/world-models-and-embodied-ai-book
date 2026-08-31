# EXP-15-01：VLA 动作合同与执行网关 smoke

fixture 将连续回归、离散 action token 和 flow action chunk 解码为同一个移动底盘动作 schema，并验证 frame、单位、时间戳、边界与 prediction/execution horizon。高层文本、过期命令、错误 frame/单位和越界动作必须被拒绝。

```bash
make ch15-test-local
make ch15-smoke-local
make ch15-smoke
```

它不运行 VLA、VLM API、机器人或仿真器，也不证明动作安全；只验证模型输出到低层控制器之间的契约。代码和 fixture 按仓库 MIT 许可发布。
