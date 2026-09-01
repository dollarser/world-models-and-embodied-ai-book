# 第15章 VLA 命令完整性审查

> 审查日期：2026-09-01
> 范围：第15章正文、`EXP-15-01` fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过；VLA/VLM、网络传输、认证、碰撞器、GPU、仿真和真实控制仍未运行

## 1. 执行时域越权

原网关只检查 packet 的 `execution_horizon` 不超过动作长度，却不检查 schema 上限。因此预测 3 步、schema 规定只执行 1 步的 chunk，可以把 packet 字段改成 3 后全部放行。v2 增加 `execution_horizon_exceeded`，packet 只能缩短或遵守 schema，不能扩大执行权限。

## 2. replay、乱序与 clock

原 packet 只有时间戳，网关无法区分同一命令重复到达、旧响应晚到或新命令。v2 加入单调 `command_id`、明确 `clock_id` 和字段顺序：已接受 7 后，重复 7 与旧命令 6 被拒绝，新命令 8 通过；wall clock 冒充控制单调 clock 以及字段交换也被拒绝。

这不是安全通信协议。fixture 不提供 session/boot ID、认证、防篡改、ACK、跨重启持久性或跨机时钟同步；生产系统必须补齐这些能力。

## 3. 一手资料核验

- OpenVLA 当前推理路径用 `unnorm_key` 选择数据集的 `q01/q99` 动作统计；代码 MIT 不覆盖 Llama 2 衍生 checkpoint 许可。
- LeRobot 异步 policy server 为 action chunk 生成 observation 起点、环境 timestep 和逐步时间戳，客户端再管理队列与重叠 chunk，说明异步执行需要显式时间身份而不只是数组。
- GR00T N1.7 主分支当前把 action dimension 扩至 132、模型 action horizon 扩至 40，并把 rollout 参数改名为 `execution-horizon`；数字随分支/checkpoint 漂移，必须读取冻结配置。
- openpi 把 normalization stats 与 checkpoint 绑定；迁移本体时需明确复用还是重算，不能凭维度猜测。

这些资料只支持接口和资源说明，本书没有运行任何上游模型。

## 4. 代码与一致性

第15章由 9 增至 15 个单元测试，全书由 220 增至 226 个。新增测试覆盖执行时域越权、packet 执行身份、replay/乱序、新命令接受、clock/字段顺序、非 mapping 输入、网关上下文和非有限动作。smoke 的 malformed packet 从 5 类扩至 10 类，实验卡升级为 fixture v2，正文、结构化结果、manifest 与发布统计同步。
