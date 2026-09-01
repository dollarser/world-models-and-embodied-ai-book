# 第10–12章练习自检审查

> 审查日期：2026-09-02
> 范围：第10–12章 17 道练习、自检答案、对应 S 档 fixture/结果及站点呈现
> 结论：通过；全书当前累计覆盖第1–12章 67 道练习，尚未覆盖第13–22章

## 1. 内容与教学结论

本轮把“表示是否可读—动作是否正确—空间是否可行动”整理成递进的自检链。第10章限制 probe 声明并加入 train/ID/shift、随机高维特征和时间负对照；第11章把 action sensitivity、响应方向、时间对齐、自由 rollout 和多主体响应拆开；第12章从射线证据、米制 footprint、观测时效、affordance、occupancy-flow、路径离散化和半开边界回答无 3D 经验读者最容易混淆的问题。

## 2. 关键准确性修正

- 无噪声 centroid fixture 中，只改变正的纹理幅度会缩放特征距离，不会让分类排名翻转；自检要求显式加入噪声、正则化或相关性改变后才能研究幅度边界；
- 第11章 `left_right_swapped` 的 action sensitivity 和 unsigned separation 与正确模型相同，但 signed separation 为 -2、counterfactual vector RMSE 约 1.633，直接证明“条件敏感”不等于“响应正确”；
- 栅格分辨率比较必须保持米制 footprint 不变。示例半宽 0.5 m 在 0.1/0.5 m 分辨率下对应保守 cell 半径 5/1，而不是复用同一 cell 半径；
- `(-0.01,0.25) m` 在 0.5 m 半开栅格中的 floor 结果为 `(-1,0)`；向 0 截断与 Python ties-to-even round 都得到 `(0,0)`，会把 x 越界点错误吸入地图；
- 第12章的 observation mask、unknown 规划语义、未来 occupancy IoU 与 footprint collision 保持分离，避免用 benchmark 计分 mask 推导可行驶空间。

## 3. 证据与资源边界

数值仅来自当前标准库 fixture 和已登记 JSON：没有运行 I-JEPA/V-JEPA、视频世界模型、3D/occupancy 网络、仿真、真实 RGB-D/驾驶数据或 GPU。随机特征、滑移、连续碰撞器和 occupancy-flow 是可执行的实验设计答案，不冒充已运行结果；驾驶阈值示例也不是安全标准。

## 4. 一致性门禁

Manifest 现登记第1–12章。机器门禁核对 67 道题与 `SELF-CHECK-NN-MM` 的章节、数量、顺序、唯一性、标签闭合和最低内容长度；严格编译站点继续验证 `<details>` 容器。第13–22章保持显式待办，不能据此发布“全书答案已完成”的声明。
