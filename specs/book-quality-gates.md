# 全书质量门禁

## 1. 门禁等级

- `BLOCK`：失败后不得合并或发布；
- `WARN`：允许继续起草，但必须进入已知限制；
- `MANUAL`：需要人工审查记录，不能由自动检查替代。

## 2. 标准命令

| 命令 | 环境 | 检查范围 | 失败等级 |
| --- | --- | --- | --- |
| `make check-local` | 宿主标准库 | 文件、JSON、链接、manifest、PRD 22 章 S 档—实验卡映射与可选 M/L 路径、22 个实验资产包、当前正文显式 `EXP/BENCH` 版本与卡片同步、声明/图表双向登记、`fact`/`inference` 证据登记、关键 `recommendation` 适用性登记、快速演进研究雷达、Mermaid 无障碍元数据、标题层级、章节教学/接口区段、读者关键术语、`result`—实验卡绑定/定义句边界与 22 组 smoke—结果精确一致性 | `BLOCK` |
| `make check-strict` | Docker | JSON Schema、manifest、实验卡/benchmark card 条件与跨资产规则 | `BLOCK` |
| `make check` | 宿主 + Docker | 依次执行 local 与 strict | `BLOCK` |
| `make docs-build` | Docker | MkDocs 严格构建、导航、Markdown 扩展 | `BLOCK` |
| `make docs-preview-check` | Docker + 宿主标准库 | 严格构建后检查 22 章产物、内部 href/src、Mermaid 无障碍元数据保留与预览入口 | `BLOCK`，发布候选必跑 |
| `make chNN-smoke` | Docker/CPU | 章节最小数据流、指标与测试 | `BLOCK`，仅针对已实现章节 |
| `make smoke-all` | Docker/CPU | 依次运行 22 章单元测试与固定 smoke | `BLOCK`，发布候选必跑 |

## 3. 提交前门禁

| 检查项 | 类型 | 通过标准 |
| --- | --- | --- |
| 基础检查 | 自动 `BLOCK` | `make check` 返回 0 |
| PRD 实验档位 | 自动 + 人工 `BLOCK` | 每章以 manifest 登记的 `EXP-NN-01` 标明已交付 S 档，并另列可选待验证 M/L 路径；不得用无档位“实验”把未运行训练或仿真写成当前交付 |
| 实验资产包 | 自动 + 人工 `BLOCK` | 每个 manifest 实验恰有一个实验卡、README、可测试源码、smoke 入口、测试和存在的结果 artifact；训练/config/独立评测入口按适用性添加，不创建 no-op 资产 |
| 正文资产版本 | 自动 + 人工 `BLOCK` | 当前 22 章正文若显式写出 `EXP-NN-NN vK` 或 `BENCH-NN-NN vK`，版本必须与对应 experiment/benchmark card 一致；历史 review 保留当时快照，不参与当前正文门禁 |
| 文档构建 | 自动 `BLOCK` | `make docs-build` 返回 0 且无 warning |
| 章节模板 | 自动 + 人工 `BLOCK` | “本章契约、小结、练习、延伸阅读、验收记录”使用独立 H2；第1–21章有“下一章接口”，第22章有“全书出口”；非适用项明确说明而非静默删除 |
| 读者术语 | 自动 + 人工 `BLOCK` | 高频缩写同时出现在作者术语基线与读者术语表；定义说明作用域和不能单独证明的结论 |
| 声明追溯 | 自动 + 人工 `BLOCK` | `CLAIM` 定义与 manifest 双向相等、类型规范、章节归属正确；每个 `result` 由同章实验卡反向绑定，外部报告数字不冒充本书结果 |
| 事实证据 | 自动 + 人工 `BLOCK` | 每个 `fact` 在 `fact-evidence.json` 登记证据基类、成熟度、锚点和支持边界；登记集与正文事实集双向相等，供应商声明不升级为独立验证；GitHub `official_asset` 必须使用完整 40 位 commit 的不可变 URL |
| 推断证据 | 自动 + 人工 `BLOCK` | 每个 `inference` 登记至少两个前提、证据锚点、反例/反证条件和适用范围；无法给出可审查前提的作者选择改为 `recommendation` |
| 关键建议 | 自动 + 人工 `BLOCK` | 会改变资源升级、数据纳入、评测发布、运行激活或安全关键执行的建议，登记适用条件、要求动作、替代/停止路径和未授权事项；登记项仍必须是正文中的 `recommendation` |
| 结果解释 | 自动 + 人工 `BLOCK` | 每个 `result` 由实验卡绑定，并在定义句直接说明不证明、不外推或只适用的边界；章节上下文解释机制而非只罗列数字 |
| 来源成熟度 | 人工 `BLOCK` | `P` 有已接收/发表的一手元数据；只有 arXiv、项目页或投稿状态时标为 `A`，官方资产 `O` 不替论文成熟度 |
| 研究雷达 | 自动 + 人工 `BLOCK` | 快速演进工作登记核查日期、一手/官方来源 revision、章节归属、资产开放度、复现状态、资源路径、不可外推边界与复核触发器；GitHub 官方仓库 URL 锁完整 commit 且与 revision 一致；作者报告不升级为本书 `result` |
| 图表追溯 | 自动 + 人工 `BLOCK` | 正文 `FIG/TAB` 与 manifest 双向相等、章节归属正确；Mermaid 有登记 ID 开头的 `accTitle` 和关系型 `accDescr`；caption、来源、许可和解释边界完整 |
| 大文件与密钥 | 自动 `BLOCK` | 不含数据、权重、缓存、密钥和敏感日志 |
| 生成资产 | 自动 `BLOCK` | 能由记录的命令重新产生 |

## 4. 章节评审门禁

| 检查项 | 类型 | 通过标准 |
| --- | --- | --- |
| 内容审查 | `MANUAL BLOCK` | 概念、公式、来源和能力边界正确 |
| 代码审查 | `MANUAL BLOCK` | 命令、测试、错误处理和资源声明一致 |
| 一致性审查 | `MANUAL BLOCK` | 正文、代码、结果、图表和实验卡相互追溯 |
| 教学审查 | `MANUAL BLOCK` | 目标读者无需未声明前置知识即可完成最小路径 |
| 失败证据 | `MANUAL BLOCK` | 至少一个失败、反例或不适用条件进入正文 |
| GPU 状态 | 自动 + 人工 `BLOCK` | 未实测内容标为待验证，不出现消费级复现误报 |

四类审查结果写入 `book-manifest.json`；达到 `reviewed` 时四项必须全部为 `passed`。

## 5. 发布候选门禁

- [ ] `make check`、`make docs-build` 和所有已实现 S 档 smoke 返回 0；
- [ ] M/L1/L2 的依赖、成本和可选性质清楚；
- [ ] 正文数字与结果资产映射完整；
- [ ] 图表 alt text、来源、许可和视觉审查通过；
- [ ] 根目录 MIT `LICENSE` 存在，发布说明准确描述原创内容和第三方资产的许可边界；
- [ ] 必做 fixture 可以合法再分发；
- [ ] 版本说明列出已验证实验、未验证声明和已知限制；
- [ ] 生成站点不包含密钥、个人数据、受限资产或失效链接。

## 6. 状态边界

- `drafted`：正文已成形，但尚未完成四类审查；
- `reviewed`：正文和可执行路径已审查，可能仍待 GPU 验证；
- `reproducible`：章节所需目标硬件实验与冷启动复现均通过；若章节不需要 GPU，状态写 `not_required`；
- `published`：发布门禁通过并生成不可变版本说明。

章节成熟度与站点发布是两条相关但不同的轴：全书可由 `reviewed` 章节组成证据范围受限的在线版本；只有完成目标硬件/数据冷启动的章节才能标为 `reproducible`。任何版本都不能把待验证的性能或资源声明作为正式结论发布。
