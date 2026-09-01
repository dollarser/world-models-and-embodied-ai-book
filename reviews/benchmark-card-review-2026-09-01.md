# Benchmark Card 机器契约与第6/9章交叉审查

> 审查日期：2026-09-01
> 范围：`specs/benchmark-card.schema.json`、三张 benchmark card、第6/9/20章、严格验证器与契约测试
> 结论：机器契约可用于冻结当前两组教学评测；不升级实验成熟度

## 1. 为什么不扩写 experiment card

现有 experiment card 记录单次运行来源、资源、命令、指标值和产物。benchmark card 记录运行前应冻结的比较问题：用途和声明边界、系统角色、数据划分、样本单位、指标方向与实现、统计方法、distribution shift、退出条件和报告粒度。把两者合并会让协议随着每次运行元数据变化，也容易在看到结果后静默改指标。

本轮因此新增独立 Draft 2020-12 Schema，并保留 `benchmark → experiment → result` 单向追溯关系。

## 2. 内容与教学审查

- `BENCH-06-01` 明确区分 posterior filtering 与 prior-only rollout，冻结 31 个转移、seed 7 和未来观测可见性；一个 seed 只算 regression fixture，不报告伪置信区间。
- `BENCH-09-01` 分开 E1 的 12 个转移和 E4 的两个 episode，登记动作集合、tie-breaking、24 步 horizon 与失败阈值；它没有 OOD estimator，明确关闭 distribution-shift 协议。
- `BENCH-20-01` 冻结八个 authored episode、两套不可直接比较的协议和 Wilson 区间假设，验证 Schema 能表达闭环比例、safety metric 与统计不确定性。
- 两张卡都同时列出允许声明和禁止声明，使零 3D/RL 经验读者能先理解“这个结果回答什么”，再阅读指标实现。
- 第9章新增 protocol/run/result 三层解释；第6章补入同一协议版本变更边界；第20章清除过期审查状态并接入机器卡，关闭三章交叉一致性待办。

## 3. 机器校验范围

Schema 条件规则覆盖：fixture 不得声明下载、确定性协议不得带 seed、随机协议至少一个 seed、统计区间必须给 confidence level、启用 OOD 必须给 score/calibration/threshold/fallback、executed 卡必须有产物。

跨资产检查覆盖：BENCH/METRIC ID 与章节一致、claim 和 experiment 已在 manifest 同章注册、benchmark/experiment 双向引用、metric layer 已声明、系统名唯一、产物存在、资源下载量等于数据集下载量。契约测试同时保留合法样例、冻结未运行样例与九类非法变体。

这些检查只证明结构和引用一致，不能证明数据代表性、指标充分性、统计假设、模型性能或安全。新增三张卡均引用既有 CPU fixture，没有运行 GPU、下载数据或生成新性能数字。`draft/frozen` 卡允许 experiment/artifact 为空，只有 `executed` 必须引用两者，从而保持“先冻结协议、后执行”的因果顺序。

## 4. 验收

阶段提交前执行：

```bash
make check
make ch06-smoke
make ch09-smoke
make ch20-smoke
make docs-preview-check
make smoke-all
git diff --check
```

本轮实际验收通过：4 个 Schema、22 张 experiment card、3 张 benchmark card、18 个 Schema 契约测试、144 个章节测试、22 组结果精确比对，以及 27 个 HTML/982 个内部目标。全部为现有 CPU/Docker 路径，不含 GPU 或外部数据运行。

## 5. 后续边界

- 当前只有三个代表性 benchmark card，不表示 22 章都需要独立 benchmark；仅在章节确实定义比较协议时新增。
- 后续真实数据卡应先以 `draft` 编写，数据许可、下载量和分组键确认后升为 `frozen`，运行产物存在后才可标记 `executed`。
- 当前无 GPU，不把机器卡的存在写成 WorldArena、Dreamer、MetaDrive 或真实车辆复现。
