# 第8章 imagined loss 累计权重审查

> 审查日期：2026-09-01
> 范围：第8章正文、`EXP-08-01` v3、fixture、测试、结果、实验卡、PRD 与 manifest
> 结论：补齐 continuation 从 return target 到 actor/critic loss weight 的第二条作用路径；不改变 Dreamer 训练、策略效果和 GPU 的未验证状态

## 1. 发现的问题

旧版已经验证终止 mask 会阻止后续 reward 回传到更早的 λ-return，也正确区分 `terminated/truncated` bootstrap。但“target 正确”并不充分：如果 imagined rollout 在终止后仍生成伪状态，而 actor/critic objective 对这些 step 等权求和，终止后的 loss 仍会污染更新。正文、实验卡和代码此前都没有登记这一条数据流。

## 2. 一手实现核查

核查时锁定 DreamerV3 作者仓库当前 HEAD `e3f02248693a79dc8b0ebd62c93683888ddaccfe`。其 [`imag_loss`](https://github.com/danijar/dreamerv3/blob/e3f02248693a79dc8b0ebd62c93683888ddaccfe/dreamerv3/agent.py#L387-L421)由 discount 与 predicted continuation 的累积乘积形成 weight，并将其用于 policy/value loss。

本书只采纳接口不变量：step $t$ 的 loss 权重取决于此前是否仍存活。没有复制作者代码，也不声称标准库函数复现其数组布局、首项约定、return normalization、loss reduction、stop-gradient 或 optimizer。

## 3. 解析反例

固定 raw loss 为 `[1,1,100]`：

| 情形 | discount | 累积权重 | 加权 loss 总和 |
| --- | --- | --- | ---: |
| 正确终止 | `[1,0,0]` | `[1,1,0]` | 2 |
| 漏掉 mask | `[1,1,0]` | `[1,1,1]` | 102 |

新增 `post_terminal_loss_leakage = 100`。这里的 100 是手工构造的非负标量，用于暴露接口错误；不是 actor/critic loss 实测、梯度大小、策略退化或样本效率。

## 4. 代码与教学边界

- `cumulative_loss_weights()` 明确第一个 step 权重为 1，后续权重是此前 discounts 的乘积；
- `weighted_loss_audit()` 拒绝空序列、长度不匹配、越界 discount、负 loss、布尔与非有限输入；
- 新增 3 个单元测试，第8章由 12 增至 15 个；
- 自动驾驶正文的碰撞/任务终止语义同时约束 return target 和 loss weighting，但本书没有运行 learned continuation、仿真或车辆；
- S 档仍为 Python 标准库、CPU、零下载，不新增 GPU 或硬件要求。

## 5. 验收门禁

```bash
make ch08-test-local
make ch08-smoke-local
make smoke-all
make check
make docs-preview-check
git diff --check
```

作者源码核查只固定概念依据，不构成上游运行或独立复现证据。
