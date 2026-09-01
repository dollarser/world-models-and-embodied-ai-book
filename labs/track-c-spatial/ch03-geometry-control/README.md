# EXP-03-01：零基础几何与反馈桥接

该实验包含三个零下载 fixture：

1. 将三个 RGB-D 像素反投影到相机坐标系，沿 camera→body→world 变换链组合并栅格化为简化 BEV；同时注入毫米/米、外参平移、非法旋转和轴映射错误。
2. 在二维双连杆机械臂中比较固定开环动作与带噪观测反馈，验证反馈能修正固定执行偏差。
3. 将同一 body-frame 点分别用采样时刻与早 100 ms 的位姿变到 world frame，分开测量平移和旋转造成的空间误差。

```bash
make ch03-test-local
make ch03-smoke-local
make ch03-smoke
```

它只验证公式、单位、时间戳和数据流，不代表真实相机标定、定位、运动补偿、动力学控制或机器人安全验收。代码和程序化 fixture 按仓库 MIT 许可发布。
