# 第12章稀疏 waypoint 与路径段验证审查

> 审查日期：2026-09-01
> 范围：第12章正文、`EXP-12-01` v3、fixture、测试、结果、实验卡、PRD 与 manifest
> 结论：修复“说明称为 swept path、实现只检查 waypoint”的代码—文档不一致；不改变连续碰撞、动力学、仿真和 GPU 的未验证状态

## 1. 发现的问题

旧版 `path_risk_report()` 的 docstring 和正文都使用“swept”描述，但实现只在输入 path tuple 的离散 waypoint 上展开 footprint。若相邻 waypoint 不相邻，中间 occupied cell 不进入检查集合，两个合法端点可能被误写成一条合法 motion。这不仅是丰富度不足，也是安全语义与代码不一致。

## 2. 一手接口依据

[OMPL state-validity 文档](https://docs.ros.org/en/iron/p/ompl/doc/markdown/stateValidation.html)区分 state validity 与 motion validity：离散 motion validator 必须按分辨率拆分状态间运动；存在 continuous collision checking 时应采用相应实现。[Nav2 Costmap 2D 文档](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/)则把 footprint 作为 costmap 路径碰撞检查的显式几何输入。

本书没有运行 OMPL/Nav2，也没有复制其实现。二者只用于确认“端点有效不蕴含路径段有效”和“中心点检查不蕴含 footprint 有效”这两个接口边界。

## 3. 修复与固定反例

`EXP-12-01` v3 默认用 Bresenham 连接每对相邻整数 waypoint，再在追踪中心格上展开方形 footprint；`interpolate_segments=False` 只作为错误基线保留。

| 查询 | waypoint | 中心格 | occupied | safe |
| --- | ---: | ---: | ---: | --- |
| waypoint-only | 2 | 2 | 0 | true |
| segment-rasterized | 2 | 3 | 1 | false |

固定路径为 `(3,3)→(3,5)`，中间 `(3,4)` 是 occupied。基线允许 unknown，因此两个 endpoint 单独检查时 safe；段栅格化检出中间障碍后拒绝。

## 4. 证据边界

- Bresenham 只追踪一个整数中心线，不是覆盖所有相交格的 supercover；
- 方形 footprint 只在离散中心格展开，没有连续姿态、转向、速度、加速度或制动距离；
- 静态 grid 没有动态对象插值和时钟不确定性；
- 新增结果不能支持 continuous collision-free、车辆可达性或道路安全结论。

## 5. 代码与门禁

- 新增 2 个独立测试，并在既有输入合同测试中拒绝非布尔插值开关；第12章由 13 增至 15 个测试；
- 报告同时输出 sampled waypoint 与 traced center-cell 分母，避免“检查了 path”却不说明采样密度；
- 更新 `CLAIM-12-10`、`TAB-12-04`、实验卡、中央结果、manifest、PRD 和发布状态；
- S 档仍为 Python 标准库、CPU、零下载、MIT fixture。

```bash
make ch12-test-local
make ch12-smoke-local
make smoke-all
make check
make docs-preview-check
git diff --check
```
