# EXP-20-01：评测协议可比性 smoke

该实验让同一个假想模型面对一张固定的 8 回合结果表，再分别应用“仅 easy、到达目标即成功”和“完整任务、安全感知成功”两套协议。成功率从 `100%` 变为 `62.5%`，审计器同时标记任务总体、成功定义和分母三项差异。完整协议另报告 `8 attempted / 8 valid / 7 terminated / 1 truncated / 0 invalid`：有效 timeout 留在失败分母，具名技术无效运行会阻止聚合，不能静默删除；双真结束标志分别计数但只贡献一个 attempted episode。

它没有运行 LIBERO、MetaDrive、CARLA 或真实机器人，不能作为任何模型的 benchmark。其用途是阻止脱离协议比较成功率。

```bash
make ch20-test-local
make ch20-smoke-local
make ch20-smoke
```

数据为仓库内程序化 fixture，下载量 0，按仓库 MIT 许可发布。
