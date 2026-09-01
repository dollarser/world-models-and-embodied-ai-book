# 研究雷达九月新进展与开放资产审查

> 日期：2026-09-02
> 范围：快速演进研究雷达、一手论文、A2World官方仓库与当前发布摘要
> 结论：新增三张有独立教学价值的卡，不把新模型数量或作者结果升级为稳定正文结论

## 发现

原雷达的五行方向表被误写成“四行”，属于结构修改后的语义漂移。已有九张卡覆盖模型用途与评测误差，但对2026年8月出现的跨本体受控反例、policy/simulator统一模型，以及同一预训练先验分化为两种用途的开源实现还没有明确位置。

## 修订

- `XEWorld`登记为 `body_candidate/R0`：价值在于held-out embodiment与解耦证据，不把被测模型的视觉相似度偏差外推成普遍不可能性；
- `Riemann-1.0`登记为 `monitor/R0`：只记录统一因果序列和双角色主张，代码、权重、数据、资源与全部性能数字保持unknown/上游报告；
- `A2World`登记为 `case_card/R1`：锁定官方仓库commit `077e10ad6cee07342b5e779f11fea78247584834`，核对Apache-2.0许可、world-model入口与部分checkpoint元数据，同时明确当前发布不等于policy路径或论文结果已独立复现。

正文雷达同步扩为十二张卡，并把总览改为六个方向。发布摘要中的严格规格测试数从旧快照59同步为当前61；这只是既有门禁计数更新，不是新实验。

## 边界

本轮只读取论文页面、远端HEAD、固定commit下README与LICENSE；没有clone仓库、安装依赖、下载checkpoint或数据、运行GPU/仿真/机器人，也没有验证任何作者报告指标。A2World的`R1`只表示公开资产接口审计，XEWorld与Riemann-1.0保持`R0`。

## 验收

```text
make smoke-all
make docs-preview-check
make check
git diff --check
```

实际结果：22章共308个章节单元测试和22组固定smoke通过，结果JSON与登记artifact精确一致；严格规格检查覆盖4个schema、22章、22张实验卡、3张benchmark card和61项测试；站点检查覆盖29个HTML、22章、23张可访问Mermaid图、116个折叠式自检和1161个内部目标；`git diff --check` 返回0。
