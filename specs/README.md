# Specs 索引

本目录保存书籍的可执行契约。PRD 回答“写什么和为什么”，这里的规格回答“怎样交付和怎样验收”。

## 产品与流程

- [当前 PRD](PRD/世界模型与具身智能_书籍设计方案-v0_6.md)
- [编写与审查执行流程](PRD/书籍编写与审查执行流程.md)
- [全书机器清单](book-manifest.json)
- [章节状态 Schema](chapter-status.schema.json)

## 内容规格

- [章节模板](chapter-template.md)
- [术语与符号](terminology.md)
- [写作风格](writing-style.md)
- [证据与声明](evidence-policy.md)
- [事实声明证据登记](fact-evidence.json)
- [图表规范](figure-guidelines.md)

## 工程与治理

- [实验卡 Schema](experiment-card.schema.json)
- [Benchmark Card Schema](benchmark-card.schema.json)
- [全书清单 Schema](book-manifest.schema.json)
- [许可、数据与密钥政策](license-and-data-policy.md)
- [全书质量门禁](book-quality-gates.md)

## 修改规则

1. 修改 Schema 时同步更新示例资产和严格校验；
2. 修改章节状态时同步更新 `book-manifest.json`；
3. 修改术语边界时审查所有已写章节；
4. Specs 变更必须说明迁移影响，不能静默降低门禁。
