# PRD—正文—实验档位一致性审查

> 审查日期：2026-09-01  
> 基线：`c465b5c` 之后的工作树  
> 范围：v0.6 PRD 的 22 章实验描述、当前 manifest、实验卡、结果与仓库结构

## 1. 发现的问题

PRD 的多处章节仍用无档位“实验”描述最初研究目标，例如直接训练 mini-RSSM、BC/ACT、Diffusion Policy、VLA，调用 V-JEPA checkpoint，或在真实仿真器与 learned world model 中比较。当前仓库实际交付的是 22 个零下载或微型数据的 CPU/Docker S 档 fixture；训练、真实数据、上游 checkpoint 和仿真仍是可选待验证 M/L 路径。

这会产生两类误读：读者可能把未运行目标当作当前交付，也可能认为无 GPU 无法走完主线。它还违背“正文、代码、实验卡和状态一致”的项目合同。

## 2. 修正

- 22 章逐一改为 `S 档（已交付，EXP-NN-01）` 与 `M/L 档（可选待验证）`；
- S 档描述直接来自当前实验卡的 `claim_scope` 和实际 fixture，不把接口/算术反例写成模型效果；
- M/L 档保留完整研究目标，并补充数据许可、版本锁定、GPU/仿真、评测和停止条件；
- 学完能力把必做 S 档接口审计与可选 M 档训练分开，不要求 GPU 才能读完全书；
- “仓库建议”改为当前真实结构，修复 part、track、scripts、results、benchmarks 与 specs 的历史目录名。

## 3. 防回归合同

`scripts/check_book.py` 新增 PRD 实验档位检查：

1. 每章必须标出 manifest 登记的 S 档实验 ID；
2. 章节不能登记不存在的 `EXP-*`；
3. 每章必须有可选待验证 M/L 升级路径；
4. 禁止重新出现无档位 `- 实验：` 描述。

两项单元测试覆盖有效映射以及缺失 S 档、陈旧实验 ID、缺失 M/L 路径和无档位实验四类失败。

## 4. 边界

本次只校准设计文档与当前交付，不声称 M/L 实验已经运行，也不删除它们作为长期研究目标。没有下载数据、checkpoint 或仿真器，没有运行 GPU、机器人或车辆。

## 5. 验证

提交前要求以下命令全部返回 0：

```bash
python3 -m unittest tests.specs.test_claim_contracts
make check
make docs-preview-check
git diff --check
```
