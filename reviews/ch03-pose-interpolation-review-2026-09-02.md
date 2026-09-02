# 第3章离散 pose 插值审查

> 审查日期：2026-09-02
> 范围：第3章 wrapped-yaw 插值、`EXP-03-01 v5`、测试、结果与机器合同
> 结论：以确定性反例补齐离散 pose bracket、角度 wrap 与禁止外推边界

## 发现与修改

原 `EXP-03-01 v4` 能量化“使用错误时刻 pose”的空间误差，但没有执行正文提到的 pose interpolation。仅检查 timestamp 接近或直接平均 pose 数组，无法发现 yaw 在 `±π` 分支切口处走错长弧。

v5 固定 `t=0/1 s` 两帧 planar pose，平移为 `x=0/2 m`，yaw 为 `+170°/-170°`。查询 `t=0.5 s` 时，预登记的线性平移与最短 yaw 弧得到 `x=1 m,yaw=180°`；直接算术平均 yaw 得到 `0°`。对 body frame 的 10 m 点，正确中点与错误中点相差 20 m。实现拒绝区间外查询、重复/倒序 timestamp 和非有限 query。

## 证据边界

20 m 是作者构造的角度、点距和无噪 pose 所决定的解析反例，不是定位误差、事故严重度或现实频率。线性平移与最短 planar yaw 弧也不等于一般 `SE(3)` interpolation；本阶段没有运行 ROS、Autoware、定位、clock synchronization、rolling shutter、LiDAR deskew、相机、车辆、机器人或 GPU。

## 验收

提交前运行第3章单元测试与 smoke、22 组结果精确比对、严格规格门禁和 `git diff --check`。通过后只提交本阶段明确文件。
