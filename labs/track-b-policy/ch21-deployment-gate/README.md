# EXP-21-01：deadline 与部署安全网关 smoke

固定 6 个延迟样本说明均值通过不代表每个控制周期满足 deadline；两组同均值、同尾延迟、同 miss rate 的序列进一步暴露连续 miss burst。固定动作 packet 分别注入旧观测、超时、非有限动作、越界动作、过期 action chunk 和过高 uncertainty score；第15/21章共同导入的 `mobile-base-v1` schema 为线速度与角速度分别提供范围、单位和单步变化限制。相邻步负对照证明两个静态合法端点仍可能违反逐字段变化限制，并在前序记录缺失、schema/单位/频率/ack 错配时 fail closed。八步异步 schedule 区分 `stale_chunk` 与 `queue_underflow`；七步成对状态机把“两次连续健康”与显式 `reactivation_authorized` 拆开，四条四步生命周期再区分 request、operation、success、timeout/failure 和授权。九例 receipt audit 进一步检查 fallback run、目标模式、声明 approver、半开有效期、决定、序号和单次消费。另一组六个手工 score/failure 对展示 risk–coverage 工作点；成对严重度负对照保持 coverage 与失败计数相同，只交换被接受的 authored low/high-consequence failure。

```bash
make ch21-test-local
make ch21-smoke-local
make ch21-smoke
```

该实验不运行模型、uncertainty estimator、网络、ROS、机器人、车辆或 GPU，也不是实时系统或安全认证。分数不是校准概率，`1/10` 后果权重只是手工无外部标定的敏感性分析代理权重，不是事故概率、伤害或成本；共享的物理单位和单步限制仍是教学 profile，手工 ack 不是可信执行器反馈，差值也不是物理加速度/jerk、动力学可行性或安全证明；离散 chunk schedule 不测调度或通信；fallback 状态名、完成/失败报告和超时阈值不证明具体动作可达、已完成、operator 可用、备用 MRM 切换或安全。receipt 的字符串/整数均为手写，去重状态只在内存中；它不实现身份认证、签名、防篡改、撤销、重启持久化或并发原子消费。代码与 fixture 按仓库 MIT 许可发布。
