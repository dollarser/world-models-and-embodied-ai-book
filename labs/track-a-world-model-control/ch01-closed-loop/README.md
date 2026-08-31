# EXP-01-01：离线误差与闭环后果 smoke

两组五步 residual action 的逐步 MAE 都是 0.1；标量动力学积分后，持续同号序列越过 0.3 教学边界，交替序列没有。

```bash
make ch01-test-local
make ch01-smoke-local
make ch01-smoke
```

实验没有图像、学习模型、反馈 controller、仿真或硬件。0.3 是手工教学阈值，不是机器人或车辆安全标准。代码和 fixture 按 MIT 许可发布。
