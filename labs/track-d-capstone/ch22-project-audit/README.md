# EXP-22-01：综合项目包审计 smoke

审计两个手工项目包 fixture：完整驾驶项目为 0 issue，并校验 train/selection/eval 在 group、原始来源、精确内容指纹和预登记近重复簇四个维度互斥，连同 5 个带 SHA-256 的 artifact binding、绑定 command/result digest 的执行回执、2 个失败注入、冻结独立评测、可追溯 safety gateway，以及 input、method、independent evaluation、deployment/safety gate、evidence package 五段 trace；故意无效包产生 24 个具名 issue。另实际启动三个不经过 shell 的固定 `python3` probe，分别得到 stdout digest 匹配、digest 漂移和非零退出。

```bash
make ch22-test-local
make ch22-smoke-local
make ch22-smoke
```

审计器会对内存中的固定文本 payload 重算摘要，并运行一个受限的标准库子进程 fixture；它不遍历真实项目目录、不重建环境、不运行模型，也不读取媒体或发现未登记近重复。author-written receipt 没有签名或独立证明，因此这些结果不证明科学正确性、真实结果复现、数据独立性、许可、隐私或安全。代码和 fixture 按 MIT 许可发布。
