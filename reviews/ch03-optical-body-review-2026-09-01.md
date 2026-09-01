# 第3章 optical/body 坐标与深度语义审查

> 审查日期：2026-09-01
> 范围：第3章正文、`EXP-03-01` 几何 fixture/测试/结果、实验卡、manifest 与发布状态
> 结论：通过；真实标定、畸变、同步、硬件与控制稳定性仍未验证

## 1. 坐标语义错误与修复

正文采用 camera optical `(right, down, forward)`，但旧 fixture 用单位旋转直接生成 body 点，再把 body `x-y` 当水平 BEV。这等价于把 optical down 当横向、optical forward 当高度；像素投影 round trip 仍为 0，因此原检查无法发现。

v2 显式采用 body `(forward, left, up)`，加入固定 `R_body_camera`：optical forward→body forward、optical right→body right、optical down→body down。三个点经正变换与逆变换后的最大误差为 8.67×10⁻¹⁸ m；故意使用单位旋转时平均 body 点误差为 2.35718 m。该反例证明像素 round trip 只验证投影实现闭合，不验证跨 frame 语义。

## 2. z-depth 与 range

旧正文默认深度沿 optical `z`，但没有提醒部分设备/API 返回欧氏射线距离。新增解析路径在归一化离轴坐标 `(1,0)` 对比：数值 1 m 的 z-depth 对应 1.41421 m range；若输入是 1 m range，则 `Z=1/sqrt(2)` m。主点处二者相同，因此只测中心像素会掩盖错误。

OpenCV 4.13 官方 calib3d 文档复核了 pinhole `K`、`Z_c` 投影、frame 变换链和刚体逆变换公式；Modern Robotics 继续作为 `SE(3)` 开放教材入口。ROS REP 页面本次浏览被站点防护拒绝，正文只保留既有规范链接，不新增未经读取的细节。

## 3. 代码与边界

第3章由 6 增至 10 个单元测试，全书由 203 增至 207 个。新增测试覆盖 optical/body 三个单位轴、刚体正逆 round trip、离轴 z-depth/range、非法内参和非有限平移。fixture v2 仍是三点理想针孔和固定正交旋转，不代表真实标定精度、畸变处理或车辆坐标正确性。
