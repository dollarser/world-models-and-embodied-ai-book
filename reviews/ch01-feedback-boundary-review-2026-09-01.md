# 第1章反馈、时延与动作权限边界审查

> 日期：2026-09-01
> 范围：第1章、`EXP-01-01`、`CLAIM-01-06`、`TAB-01-03`
> 结论：通过当前 S 档的内容、代码、一致性与教学审查

## 为什么需要本轮增强

原第1章已证明“相同逐步 MAE 不唯一决定积分后果”，但实验只有 residual 积分，无法回答初学者紧接着会问的问题：既然误差会累积，反馈能否纠偏；有反馈为什么仍会失败。若不补这一层，正文从闭环框图直接跳到后续规划、仿真和部署，容易让读者把“存在 controller”误读为“已具备闭环保证”。

## 固定模型与边界语义

本轮增加确定性标量模型：

\[
x_{t+1}=x_t+u_t+d_t,\qquad
u_t=\operatorname{clip}(-k\tilde{x}_t,-u_{\max},u_{\max}).
\]

- 12 步 disturbance 固定为 `0.1`；
- 边界固定为 `abs(x) > 0.3`，等于 `0.3` 不算越界；
- observation delay 以离散步计；历史不足时观测初始 state `0.0`；
- saturation 统计 `raw_action` 超出 `[-action_limit, action_limit]` 的步数；
- 所有量均无物理单位，不映射车辆横向、机器人关节或任何执行器。

## 固定结果

| case | gain | delay | limit | maximum | final | first violation | saturation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| open loop | 0.0 | 0 | 0.25 | 1.2 | 1.2 | 4 | 0 |
| timely feedback | 0.8 | 0 | 0.25 | 0.124999999488 | 0.124999999488 | — | 0 |
| delayed feedback | 0.8 | 2 | 0.25 | 0.4076 | 0.4076 | 4 | 1 |
| authority-limited feedback | 0.8 | 0 | 0.05 | 0.65 | 0.65 | 6 | 11 |

无时延、未饱和 case 的固定点为 `d / k = 0.125`。这为及时反馈的残余误差提供解析解释；它不能外推到带时延或持续饱和的 case。

## 解释边界

- `delayed feedback` 是有限 12 步反例；没有特征根或 Lyapunov 分析，正文不声称一般不稳定。
- `authority-limited feedback` 只说明请求动作与可执行权限必须分开；不声称真实 actuator 必然出现相同结果。
- fixture 没有 observation noise、estimator、动力学、接触、learned policy、真实 clock 或 safety case。
- `CLAIM-01-06` 仅绑定本书结果 JSON 和实验卡，不把 MIT 课程资料当作本书数值复现。

## 来源核查

- [MIT Underactuated Robotics: Output Feedback](https://underactuated.mit.edu/output_feedback.html)：用于支撑 measurement/output feedback 与 estimator dynamics 会影响闭环的概念背景。
- [MIT Underactuated Robotics: The Simple Pendulum](https://underactuated.mit.edu/pend.html)：用于支撑 torque/action limit 会约束可实现控制的概念背景。

两项均为开放课程一手材料。正文采用转述并明确它们不验证本 fixture 的具体数字。

## 资产与审查结论

- 源码：`labs/track-a-world-model-control/ch01-closed-loop/src/closed_loop_fixture.py`
- 测试：第1章由 6 个增加到 10 个，覆盖及时反馈、两步时延、动作权限和非法输入。
- smoke：同时验证 timely case 不越界、delayed case 越界、limited case 饱和 11 步。
- 结果：`results/ch01/EXP-01-01-smoke.json` 保存完整 observation/raw action/action/state trace。
- 实验卡、manifest、PRD、正文声明和图表登记同步为 fixture v2。

阶段门禁已通过：`make smoke-all` 覆盖全书 266 个章节测试，`make check` 覆盖 52 项严格规格测试并精确比对 22 组 smoke 结果，`make docs-preview-check` 验证 28 个 HTML、22 章、23 张可访问 Mermaid 图和 1073 个内部目标；`git diff --check` 无格式错误。
