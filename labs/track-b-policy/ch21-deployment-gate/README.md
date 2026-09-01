# EXP-21-01：deadline 与部署安全网关 smoke

固定 6 个延迟样本说明均值通过不代表每个控制周期满足 deadline；两组同均值、同尾延迟、同 miss rate 的序列进一步暴露连续 miss burst。固定动作 packet 分别注入旧观测、超时、非有限动作、越界动作、过期 action chunk 和过高 uncertainty score；八步异步 schedule 区分 `stale_chunk` 与 `queue_underflow`；七步成对状态机把“两次连续健康”与显式 `reactivation_authorized` 拆开，三条四步生命周期再区分 request、operation、success、timeout/failure 和授权。另一组六个手工 score/failure 对展示 risk–coverage 工作点。

```bash
make ch21-test-local
make ch21-smoke-local
make ch21-smoke
```

该实验不运行模型、uncertainty estimator、网络、ROS、机器人、车辆或 GPU，也不是实时系统或安全认证。分数不是校准概率；离散 chunk schedule 不测调度或通信；fallback 状态名、完成/失败报告、超时阈值和手工授权信号不证明具体动作可达、已完成、operator 可用、真实授权、备用 MRM 切换或安全。代码与 fixture 按仓库 MIT 许可发布。
