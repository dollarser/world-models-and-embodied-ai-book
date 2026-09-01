# 第3章时间对齐与运动补偿边界审查

> 审查日期：2026-09-01
> 范围：第3章正文、`EXP-03-01` v4、fixture、测试、结果、实验卡、PRD 与 manifest
> 结论：补齐“时间戳是几何合同的一部分”的可计算反例；不改变真实传感器、ROS、Autoware、定位或运动补偿的未验证状态

## 1. 发现的问题

旧正文已经要求 timestamp 和时间偏移注入，也指出错误时间戳会造成点云拖影，但 `EXP-03-01` 只覆盖静态外参、轴映射、深度语义和二维反馈。读者无法从现有结果回答：“100 ms 的位姿错位究竟会造成多大空间误差？”此外，状态页仍写第3章 10 个测试，而前一轮 proper-rotation 增强后实际已是 12 个。

## 2. 教学模型与修复

新增标准库解析夹具，把 body 点分别使用传感器采样时刻和过期位姿时刻变到 world frame：

- 仅常数 world-x 平移时，$\epsilon_{trans}=|v_x||\Delta t|$；
- 仅常数 yaw 时，距离旋转中心 $r$ 的点满足 $\epsilon_{rot}=2r\sin(|\omega\Delta t|/2)$；
- 平移和转动是独立教学对照，不宣称一般 `SE(3)` 误差可以直接相加；
- 匹配 timestamp 是零误差基线，而非真实定位精度证据。

正文进一步拆开 clock offset、消息延迟、scan/rolling-shutter 内部采样跨度和 pose interpolation。ROS 2 [`tf2` time travel](https://docs.ros.org/en/lyrical/Tutorials/Intermediate/Tf2/Time-Travel-With-Tf2-Cpp.html)显式区分 source time、target time 与 fixed frame；Autoware [`distortion_corrector`](https://autowarefoundation.github.io/autoware_universe/pr-10077/sensing/autoware_pointcloud_preprocessor/docs/distortion-corrector/)按点时间戳结合 twist/IMU 做运动补偿，其[多 LiDAR 拼接文档](https://autowarefoundation.github.io/autoware_universe/main/sensing/autoware_pointcloud_preprocessor/docs/concatenate-data/)也把时间同步和 motion compensation 作为独立接口。它们用于校准概念边界，本书没有安装或运行这些系统。

## 3. 固定结果与边界

| 对照 | 固定输入 | 空间误差 |
| --- | --- | ---: |
| 仅平移 | $v_x=2$ m/s，$t_s=1.0$ s，$t_p=0.9$ s | 0.20 m |
| 仅转动 | $r=10$ m，$\omega=0.5$ rad/s，相同时间偏移 | 0.499947918294 m |
| 时间匹配 | $t_s=t_p=1.0$ s | 0 m |

这些值来自常速度、常 yaw、单点、精确 timestamp 的手工模型。它们不是 localization、clock synchronization、pose interpolation、rolling-shutter correction、LiDAR scan deskew、动态物体补偿或真实传感器精度结果。组合运动、三维角速度和不确定位姿需要完整的时变 `SE(3)` 处理。

## 4. 代码与一致性审查

- 新增 4 个测试，覆盖平移公式、转动弦长、匹配时间和非法/非有限输入；第3章当前为 16 个测试；
- `smoke.py` 明确断言 0.20 m 与 0 m 两个边界，并把三个时间对齐结果写入中央 JSON；
- 新增 `CLAIM-03-09` 与 `TAB-03-04`，同步实验卡、manifest、PRD、状态和发布说明；
- 实验仍为零下载、CPU、Python 标准库 S 档，不新增 GPU、Docker 镜像、数据或硬件要求。

## 5. 验收门禁

```bash
make ch03-test-local
make ch03-smoke-local
make smoke-all
make check
make docs-preview-check
git diff --check
```

门禁只证明仓库内解析夹具、文档合同和编译站点一致；应用内浏览器的多尺寸、深浅色、键盘和屏幕阅读器人工巡检仍是发布操作，不由本次代码测试替代。
