# 编译站点语义可访问性审查

> 日期：2026-09-02
> 范围：29个MkDocs编译页面、生成站点检查器与发布门禁
> 结论：补齐可自动验证的HTML语义合同，人工视觉与辅助技术巡检仍未完成

## 发现

当前Material主题已经生成`lang="zh"`、device-width viewport、skip link、main landmark和单一H1，但原门禁只检查链接、Mermaid元数据和练习自检。主题或配置升级后，即使语言退回英文、skip link失效或图片丢失alt，原检查仍可能通过。

应用内浏览器当时可显示本地页面，但当前任务没有可调用的浏览器控制接口，因此没有获得可信的窄屏、深浅色、键盘或屏幕阅读器证据。本轮不把DOM检查写成视觉验收。

## 修订

`scripts/check_site.py`现在逐页要求：恰好一个`lang="zh"`、一个device-width viewport、一个`main`、一个H1，以及所有`img`具有非空alt；28个正文页面还必须有一个指向本页现存ID的skip link。主题的短404页没有skip link，首轮新门禁准确发现这一差异；修订后仅对该页显式豁免，并新增404接受测试，未放宽正文页面。质量门禁和状态页同步说明覆盖范围。

## 边界

这些检查能发现结构回退，不能证明色彩对比度、窄屏表格滚动、焦点可见性、朗读顺序、数学公式或Mermaid在真实辅助技术中的体验。后续浏览器接口可用时仍需完成截图式多尺寸和键盘/屏幕阅读器人工巡检。

## 验收

```text
make smoke-all
make docs-preview-check
make check
git diff --check
```

实际结果：22章共308个章节单元测试和22组固定smoke通过，结果JSON与登记artifact精确一致；严格规格检查覆盖4个schema、22章、22张实验卡、3张benchmark card和61项测试；3项站点语义单元测试通过；站点检查覆盖29个HTML、22章、23张可访问Mermaid图、116个折叠式自检、1161个内部目标和语义可访问性合同；`git diff --check`返回0。
