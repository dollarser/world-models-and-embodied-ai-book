# EXP-04-01：数据契约审计

该实验对一个有效 fixture 和一个注入错误的 fixture 执行 metadata 审计，覆盖时间频率、frame index、动作范围、自然终止/外部截断、显式缺帧 mask、多传感器时间偏差、归一化范围，以及跨 split 的 group、原始来源、精确内容指纹和近重复簇重叠。v5 进一步把 normalization artifact 绑定到 source episode 与 content fingerprint，并从原始 train state 重算 sample count、逐维 mean 和 population scale，避免只相信 `normalization_scope=train` 标签。

```bash
make ch04-test-local
make ch04-smoke-local
make ch04-smoke
```

实验不下载真实 LeRobot 或驾驶数据；通过 smoke 只证明审计规则能够识别已注入问题。`valid=false, timestamp=null` 是允许的显式传感器缺失；缺少整个传感器记录不会被当作同一件事静默接受。

`content_fingerprint` 只代表由数据管线预先写入的精确身份，`similarity_cluster_id` 只代表预先计算或人工审核后的近重复分组。审计器不会读取媒体、计算 perceptual hash/embedding 或判断两个样本在语义上是否相似；真实数据必须冻结生成方法、版本与阈值，并人工复核边界样本。

统计重算只覆盖两维、三个样本的无 mask 程序化 state，不代表真实分布估计、robust statistics、角度/四元数处理、分布式数据管线或 checkpoint compatibility。
