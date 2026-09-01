# 实验资产最小合同审查

> 审查日期：2026-09-01  
> 基线：`04de219` 之后的工作树  
> 范围：PRD 代码与复现规范、执行流程、实验卡 Schema、22 个实验目录和中央结果资产

## 1. 发现的问题

PRD 仍使用旧版 `experiment-card.yaml`，并要求每个实验都创建 `config/`、`prepare/train/eval/report` 和目录内 `results/reference/`。当前实现已采用 `experiment-card.json`、根目录 `results/chNN/` 和统一 Schema；22 个 S 档中多数是解析或 metadata fixture，没有训练步骤。

旧写法会诱导两种低质量实现：为不适用的训练阶段创建 no-op 脚本，或在实验目录与中央结果目录维护两份数字。它也把执行阶段 `learn/evaluate/stress/report` 与实验卡状态混为一谈。

## 2. 修正后的合同

所有已登记实验共同要求：

- `README.md`；
- `experiment-card.json`；
- 至少一个 `src/*.py` 可测试模块；
- `scripts/smoke.py`；
- 至少一个 `tests/test_*.py`；
- 实验卡指向存在的中央 `results/chNN/` 结构化结果。

`config/`、数据准备、训练、独立 evaluate/report、checkpoint 和外部数据元数据按实验适用性添加。训练型实验必须分离 train 与 evaluate；纯解析/metadata fixture 可让 smoke/evaluate/report 复用同一个确定性入口，但不能缺少结构化结果和限制。

实验卡状态统一为 `planned → smoke → experimented → reviewed → reproducible`。执行阶段不是状态；S 档 smoke 也不会自动升级为训练效果、鲁棒性或安全证据。

## 3. 自动检查

`scripts/check_book.py` 新增实验资产包检查，保证 manifest 和实验卡集合双向一致、ID 不重复、共同文件存在、源码与测试非空、结果 artifact 存在。两项单元测试覆盖完整最小包和陈旧/缺失包。

当前 22 个实验包全部通过。检查特意不要求 `config/` 或 `train`，以免形式主义压过实验语义。

## 4. 保留边界

资产存在与 smoke 通过只证明当前 S 档接口可运行，不证明 M/L 训练、目标硬件资源、上游项目、仿真器或真实系统可复现。训练型实验一旦加入，仍须补齐配置、数据、环境、seed、checkpoint 和独立评测。

## 5. 验证

提交前要求以下命令全部返回 0：

```bash
python3 -m unittest tests.specs.test_claim_contracts
make check
make docs-preview-check
git diff --check
```
