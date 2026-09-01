# 当前正文实验与基准版本一致性审查

> 日期：2026-09-02
>
> 范围：22 章当前正文、22 张 experiment card、3 张 benchmark card、`scripts/check_book.py` 与严格规格测试

## 发现的问题

实验 fixture 迭代时，正文中的显式版本不会自动随实验卡升级。本次扫描发现：

- 第2章三处仍把当前 `EXP-02-01` 写成 v2，而实验卡已是 v3；
- 第21章 burst 对照仍写 v3，fallback lifecycle 仍写 v5，而实验卡已是 v6；
- 历史 review 中的旧版本号记录的是当时审查快照，不属于错误，也不应被批量改写。

陈旧版本不一定改变局部数字，但会破坏读者从正文定位到当前代码、结果和实验卡的身份链，因此属于内容准确性与文档—代码一致性问题。

## 修复与门禁

- 第2章能力矩阵和结果声明统一指向 `EXP-02-01` v3；
- 第21章 burst 与 lifecycle 当前结果统一指向 `EXP-21-01` v6；
- 新增 `check_documented_asset_version_contract`，只扫描 manifest 登记的 22 章当前正文；
- 它解析显式 `EXP-NN-NN vK`、`BENCH-NN-NN vK` 及 benchmark JSON 写法，把 `fixture-vK` 与 `vK` 规范化比较；
- 显式版本陈旧或 ID 没有注册卡片时阻塞 `make check-local`；未写版本的普通交叉引用不报错；
- 新增 3 项规格测试，覆盖 experiment、benchmark、陈旧、未注册和无版本引用。

严格规格测试由 52 项增至 55 项。当前正文扫描为 0 个版本不一致。

## 边界

- 门禁只检查与 ID 相邻的显式版本，不推断自然语言中的“最新版”“当前版本”等模糊说法；
- experiment card 的 `data.version` 与 benchmark card 的 `protocol.version` 被视为当前权威值，门禁不证明这些卡片本身的科学内容正确；
- 历史 review、release snapshot 和旧 PRD 保留当时事实，不要求伪装成当前快照；
- 版本一致只证明身份链接正确，不证明 smoke、训练、外部数据或目标硬件结果可复现。
