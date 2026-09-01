# 全书折叠自检 Markdown 渲染审查

> 日期：2026-09-02
> 范围：22章122个 `SELF-CHECK`、MkDocs 编译产物、源码/站点门禁与发布状态

## 发现

原源码使用裸 `<details>` 包裹 Markdown 答案。浏览器能够折叠和展开，但 Python Markdown 按 HTML block 处理其内部内容：反引号、强调、列表和公式保持原始文本，没有生成与正文一致的 `<code>`、段落或数学渲染入口。原站点检查只确认 `details` 容器和 ID 没丢失，因此会把“结构存在但正文未编译”误判为通过。

第7章抽查提供了直接证据：修复前编译 HTML 在 `SELF-CHECK-07-06` 内仍包含字面量反引号；给容器增加 `markdown="1"` 后，同一答案生成 `<p>` 与 `<code>`，折叠语义保持不变。

## 修正

- 22章122个自检容器统一改为 `<details markdown="1">`；
- `check_book.py` 继续检查编号、双向覆盖、顺序、闭合和最低长度，并新增源码属性门禁；
- `check_site.py` 逐个解析编译后的自检块，要求数量与源码一致，且不得残留原始 Markdown 反引号；
- 新增严格规格负例，证明内容足够长但缺少 `markdown="1"` 仍会被拒绝；
- 质量门、执行流程、状态与发布说明同步记录真实合同。

## 验收

```bash
python3 -m unittest tests.specs.test_claim_contracts tests.test_check_site
make docs-preview-check
make check
git diff --check
```

预期当前口径：336个章节测试、68项严格规格测试、29个HTML、22章、23张可访问 Mermaid、122个已渲染 Markdown 的折叠自检、1161个内部目标。

## 剩余边界

自动检查证明源码声明了 Markdown-in-HTML 且编译块不再残留反引号，不证明所有深浅色、窄屏、键盘焦点、公式溢出或真实屏幕阅读器体验均合格。应用内浏览器控制接口在本轮不可调用，因此没有把程序化视觉点击或截图冒充已完成；本地服务与具体编译 HTML 已通过 HTTP 回查。
