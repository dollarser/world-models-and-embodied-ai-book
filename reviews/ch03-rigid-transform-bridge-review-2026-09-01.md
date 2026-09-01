# 第3/10/11/12章零基础 3D 与刚体变换桥接审查

> 审查日期：2026-09-01
> 审查基线：`3ce374d`
> 范围：第3、10、11、12章，glossary，`EXP-03-01` v3，fixture、测试、结果、实验卡与 manifest
> 结论：补齐零3D经验读者的量纲递进，并阻止任意 `3×3` 数组伪装成刚体旋转；不改变真实标定、GPU或硬件的未验证状态

## 1. 发现的问题

第3章已经区分 optical/body 轴和 z-depth/range，但旧 fixture 的 `transform_point` 只检查 rotation 是有限 `3×3` tuple。缩放、剪切甚至 determinant 为 -1 的镜像矩阵都能进入 `inverse_transform`，后者又直接用转置当逆。这与正文“刚体变换”的语义不一致，也会给初学者造成“shape 对就能当外参”的错觉。

横向阅读还发现：glossary 只有宽泛的 `frame`、pose、BEV 和 occupancy，没有分开 coordinate frame 与 video frame，也没有内参、外参、proper rotation、optical frame、z-depth/range、点云和 voxel。第10章的 depth probe、第11章的视频位移与第12章的空间查询之间因此缺少明确的量纲桥。

## 2. 修复

- `EXP-03-01` v3 校验 $R^\top R=I$ 与 `det(R)=+1`，明确拒绝缩放、剪切和镜像；
- 新增刚体变换组合：`T_world_camera = T_world_body @ T_body_camera`，验证三点逐段执行和组合执行的最大差为 0 m；
- 第3章新增像素、深度/range、camera point、body point、pose/transform、voxel/BEV cell 六级表，并说明组合平移必须先换 frame；
- 第10章要求 depth probe 登记 z-depth/range/disparity/相对深度、内参、尺度、mask、frame 和单位；
- 第11章明确像素位移不能直接解释为 body/map frame 的米制运动；
- 第12章给出零基础首读的五问路径；
- glossary 新增八个几何术语，消除 coordinate frame 与 image/video frame 歧义。

[OpenCV 相机标定与三维重建文档](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)把相机矩阵、畸变和外参作为不同参数；[Open3D 当前 RGB-D/point-cloud 示例](https://www.open3d.org/docs/latest/python_example/geometry/point_cloud/index.html)也显式传入 intrinsics、`depth_scale` 与 `depth_max`。[ROS REP-103](https://www.ros.org/reps/rep-0103.html) / [REP-105](https://www.ros.org/reps/rep-0105.html)则说明 optical/body 轴和 map/odom/base frame 属于约定，不能从数组 shape 推断。本章仍自行声明 fixture 约定，不把任何库的默认值扩展为通用事实。

## 3. 结果与边界

- 第3章由 10 增至 12 个单元测试，全书由 254 增至 256 个；
- 新测试覆盖变换链组合一致性，以及 scaling/reflection/shear 非 rotation 的拒绝；
- `max_transform_chain_gap_m = 0.0` 来自三个精确程序化点，不代表真实标定、定位精度或浮点库的一般误差；
- 原有 1000× 深度单位、0.10 m 外参平移、optical/body 轴映射、z-depth/range 与控制反例保持不变。

## 4. 门禁

本阶段要求以下命令全部返回 0：

```bash
make ch03-test-local
make ch03-smoke-local
make smoke-all
make check
make docs-build
make docs-preview-check
git diff --check
```

实际验收为 256 个章节测试、22 组 smoke 结果精确比对、4 个 Schema、22 张 experiment card、3 张 benchmark card，以及 27 个 HTML、22 章页面、994 个内部目标全部通过。

没有安装 OpenCV、Open3D 或 ROS，也没有下载点云/视频数据；一手资料只用于校准术语和接口边界。
