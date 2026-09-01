# EXP-12-01：三态 occupancy 与可行动空间 smoke

程序化深度射线在 `7×7` BEV 上标记：返回点前方为 `free`、返回点为 `occupied`、遮挡后方与视野外为 `unknown`。实验进一步检查：

- 可达 free cell 与障碍邻接形成的 approach affordance；
- 一格坐标偏移对 occupied IoU 的影响；
- 把 unknown 当 free 如何造成动态路径“假安全”；
- 动态回波离开后，旧格在没有清空射线时为何回到 `unknown`；
- 米制点怎样按 `origin / resolution / axis order / half-open boundary` 映射到 cell，以及负坐标使用 `int()` 截断为何会被误收进第 0 格；
- 稀疏 waypoint 为什么必须补查中间栅格；
- 栅格化中心线、带 footprint 的扫掠区域和过期观测为何给出不同路径判定。

```bash
make ch12-test-local
make ch12-smoke-local
make ch12-smoke
```

它不是学习式 3D 感知、抓取规划或自动驾驶安全验证。固定 0.5 m 的半开区间索引不是 ROS/Nav2 实现，Bresenham 段栅格化也不是连续碰撞检测。代码与程序化 fixture 按仓库 MIT 许可发布。
