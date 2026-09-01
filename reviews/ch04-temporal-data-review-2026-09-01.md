# 第4章时序数据合同增强审查

> 审查日期：2026-09-01
> 范围：第4章正文、`EXP-04-01` v2、两份 metadata fixture、审计器、测试、实验卡与结果
> 结论：terminated/truncated、显式传感器 mask 与同步偏差已进入 S 档；实验仍为 `smoke`

## 1. 内容准确性

- Gymnasium 官方 time-limit 文档区分任务定义内的 termination 与外部 truncation，并说明常见 value target 只在 termination 关闭 bootstrap。本章同时补充限制：截断后的最终观测若不存在或无效，不能凭语义虚构 bootstrap 输入。
- ROS 2 `message_filters` 以消息 header timestamp 配对，approximate sync 用秒级容差。本章不把容差内配对写成硬件同时曝光，并保留 clock offset/drift、rolling shutter 与 motion compensation 的未验证边界。
- LeRobot v3 官方文档确认多 episode 文件由 metadata 恢复边界，当前 API 提供按秒窗口与同步容差；本书只借鉴合同字段，没有下载或运行真实数据。

## 2. 代码与反例

有效 fixture 现含一个自然终止 episode、一个外部截断 episode、两个相机流和一个显式缺失样本。缺失样本必须写为 `valid=false, timestamp=null`；删除必需传感器记录会得到 `missing_sensor_record`。

注入 fixture 固定八类错误：动作越界、结束标志冲突、跨 split group 泄漏、缺少传感器记录、frame index 不连续、统计泄漏、sensor skew 超限和主时间 cadence 错误。审计器另有回归测试覆盖非末帧结束、缺少结束标志、sensor timestamp 非单调，以及 action/sensor timestamp 的 NaN/Inf。

旧实现存在一个正文—代码缺口：正文声称检查 NaN，但 Python 中 NaN 的范围比较不会返回越界。v2 改为先做 finite 检查，避免 NaN 静默通过。

## 3. 一致性与教学边界

- 正文数字、实验卡和 `results/ch04/EXP-04-01-smoke.json` 映射到同一 v2 fixture。
- 新术语进入作者规范和读者术语表，并与第8章 continuation、第20章 episode denominator 保持一致。
- `valid fixture = 0 issue` 只表示它符合本审计器已编码规则，不证明真实数据正确。
- 当前没有视频解码、真实 clock domain、漂移、硬触发、标定、隐私、许可或 LeRobot 数据运行，也没有 GPU 需求。

## 4. 验收

阶段提交前执行：

```bash
make ch04-test-local
make ch04-smoke
make check
make docs-preview-check
make smoke-all
git diff --check
```

实际验收结果：第4章 13 个测试、全书 152 个章节测试、18 个 Schema 契约测试、22 组结果精确比对、4 个 Schema/22 张 experiment card/3 张 benchmark card，以及 27 个 HTML/986 个内部目标全部通过。运行范围仍是 CPU/Docker fixture，不含 GPU、真实传感器或外部数据。
