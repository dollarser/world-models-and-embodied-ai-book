# EXP-16-01：跨本体动作适配 smoke

两个二维动作张量拥有相同 shape，但 `delta_x` 分别使用 controller delta unit 与厘米，夹爪正负含义也相反。实验比较直接混合 raw action 与先转换到 `(delta_x_m, gripper_open_fraction)` 规范空间再混合；另用两个手工数据集对比 dataset、episode 与 transition 三种均匀采样单位，并验证三步 action horizon 丢弃不完整窗口后，短来源会从非零 raw-transition 暴露变成零个可训练窗口。

```bash
make ch16-test-local
make ch16-smoke-local
make ch16-smoke
```

每条记录绑定由本体 ID、字段顺序、单位、缩放、夹爪极性和 canonical schema 计算的 adapter fingerprint；缺失本体、缺失 fingerprint 与陈旧 fingerprint 均被拒绝。

它不训练策略，也不证明跨本体正迁移；只验证 schema adapter、round-trip、版本身份门禁、解析采样分母与 stride-one/drop-tail 窗口计数。episode 长度、来源规模和暴露比例都是手工 fixture，不是 Open X-Embodiment、Octo 或 LeRobot 的实测分布；也没有覆盖 padding、mask、过滤、分布式 shard 或梯度权重。fingerprint 不是安全签名，也不证明数据真实性或 controller 可执行性。代码和程序化 fixture 按仓库 MIT 许可发布。
