# 第12章米制栅格与 occupancy 任务边界审查

> 审查日期：2026-09-02
> 范围：第3→12章空间接口、`EXP-12-01` v4、自动驾驶 occupancy 研究锚点、manifest/PRD/结果与发布统计
> 结论：补齐零 3D 经验读者从米制点到有限栅格的最后一道接口，并把当前估计、未来预测、动作条件世界模型和 4D 场景生成分开；未运行模型、数据、GPU、仿真或外部地图栈

## 1. 教学与准确性缺口

原正文已覆盖反投影、frame、三态 occupancy、footprint 和路径段，但从“共同 frame 中的米制点”直接跳到整数 cell，没有明确：

- `origin / resolution / axis order / finite extent`；
- cell 的半开边界；
- 负坐标必须用 floor，而不是向 0 截断；
- 数学 `(x_index,y_index)` 与数组 `[row,column]` 不能静默互换。

这不是排版细节。点 `(-0.01,0.25) m` 位于原点之外；在 0.5 m 栅格中 floor 给出 `(-1,0)`，向 0 截断却给出界内 `(0,0)`，会造成假纳入。上边界 `x=3.5 m` 在 7 格半开地图中应映射到 `(7,0)` 并拒绝。

## 2. S 档负对照

`EXP-12-01` 升级为 v4，新增 `world_to_cell`、`cell_center`、显式 bounds check 与边界报告：

- 正常点 `(0.75,0.25) m ↔ cell (1,0)`；
- 负边界 floor `(-1,0)` / out-of-bounds，对照截断 `(0,0)` / in-bounds；
- 半开上边界 `(7,0)` / out-of-bounds；
- 非有限坐标、零分辨率和布尔型分辨率被拒绝。

第12章由 15 增至 19 个单元测试，全书由 304 增至 308 个；新增 `CLAIM-12-11` 与 `TAB-12-05`，中央结果和实验卡保持精确一致。固定 0.5 m fixture 不是 ROS/Nav2 costmap 实现，也不是连续碰撞或定位验证。`0.5` 可由二进制浮点精确表示；任意十进制分辨率仍需固定 dtype、量化/容差策略和边界两侧测试，本轮没有把该问题伪装成已解决。

## 3. 快速演进研究的任务边界

一手来源复核后新增 `TAB-12-06`：

- [UniOcc（ICCV 2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_UniOcc_A_Unified_Benchmark_for_Occupancy_Forecasting_and_Prediction_in_ICCV_2025_paper.html)明确区分 current-frame occupancy prediction 与基于历史的 future forecasting，并提供 flow；
- [Drive-OccWorld（AAAI 2025）](https://ojs.aaai.org/index.php/AAAI/article/view/33010)将动作条件的未来 occupancy/flow 接到规划 cost；
- [DynamicCity（ICLR 2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/6506964d22ede4d36adae956e6a9919a-Abstract-Conference.html)面向条件化 4D occupancy generation。

正文只登记它们的任务接口，不引用作者性能数字，不把生成样本当当前状态估计，也不把 plausible future 当作已验证反事实或 simulator fidelity。本书未运行这些资产，统一标为 `R0`。

## 4. 一致性与剩余边界

- manifest 新增 `CLAIM-12-11`、`TAB-12-05`、`TAB-12-06`；
- PRD、README、实验卡、中央结果、状态和发布说明同步至 v4；
- 第12章当前结果声明为 8 条，全书为 180 条声明、91 条 `result`；
- 深浅色、窄屏、缩放、键盘和屏幕阅读器视觉验收仍待应用内浏览器控制接口可用后执行；本轮不把本地页面已打开冒充人工验收。

本轮没有下载数据、安装 3D/ROS/仿真环境、使用 GPU 或购置硬件。
