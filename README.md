# 《世界模型与具身智能：从表征、预测到行动》

面向计算机视觉算法工程师的开源教材与可复现实验书。

全书 22 章正文和对应 S 档实验骨架均已接入并完成四类审查，当前为证据范围受限的在线发布候选。当前开发设备无 GPU，只运行 Docker/CPU smoke 和微型 fixture；GPU 与大数据实验明确延后。

## 当前入口

- [书籍设计方案](specs/PRD/世界模型与具身智能_书籍设计方案-v0_6.md)
- [编写与审查流程](specs/PRD/书籍编写与审查执行流程.md)
- [可执行 Specs 索引](specs/README.md)
- [第1章从看见到行动](docs/part-01-loop/ch01-from-seeing-to-acting.md)
- [第2章定义与边界](docs/part-01-loop/ch02-what-is-a-world-model.md)
- [第4章实验协议](docs/part-01-loop/ch04-data-and-protocols.md)
- [第5章生成式预测基础](docs/part-02-world-models/ch05-generative-foundations.md)
- [第6章纵向样章](docs/part-02-world-models/ch06-rssm.md)
- [第7章模型规划](docs/part-02-world-models/ch07-model-based-planning.md)
- [第8章 Dreamer 与想象学习](docs/part-02-world-models/ch08-imagination-learning.md)
- [第9章评测样章](docs/part-02-world-models/ch09-evaluation.md)
- [第17章世界模型与策略效用](docs/part-05-fusion/ch17-world-model-policy-utility.md)
- [第18章 VLA 后训练与 World-Action Models](docs/part-05-fusion/ch18-vla-post-training-and-wam.md)
- [第19章物理仿真与 Sim2Real](docs/part-06-systems/ch19-physical-simulation-and-sim2real.md)
- [第21章部署、实时性与安全边界](docs/part-06-systems/ch21-deployment-realtime-and-safety.md)
- [第22章可审计综合项目](docs/part-07-capstone/ch22-auditable-capstone.md)
- [批次 A 四类交叉审查](reviews/batch-a-review.md)
- [批次 B 四类交叉审查](reviews/batch-b-review.md)
- [全书终审与发布候选审查](reviews/final-book-review.md)
- [章节状态](docs/status.md)
- [发布候选说明](docs/release-notes.md)

## 最小命令

```bash
make check
make smoke-all
make ch01-smoke-local
make ch06-smoke-local
make ch09-smoke-local
make ch02-smoke-local
make ch04-smoke-local
make ch08-smoke-local
make ch18-smoke-local
make ch22-smoke-local
```

优先使用 Docker：

```bash
make ch06-smoke
make ch01-smoke
make ch09-smoke
make ch02-smoke
make ch04-smoke
make ch08-smoke
make ch18-smoke
make ch22-smoke
make docs-build
```

首次构建 Docker 镜像会下载轻量 Python/文档依赖，不会下载模型权重或实验数据集。

查看严格编译后的在线书：

```bash
make docs-preview
```

该命令先用 Docker 执行 `mkdocs build --strict`，再将生成的 `site/` 只绑定到 `http://127.0.0.1:8000/`。它用于发布前视觉审查；需要边写边刷新的开发模式仍使用 `make docs-serve`。

## 状态边界

- `reviewed`：正文和 CPU smoke 已审查，但可能仍待 GPU 验证；
- `reproducible`：目标硬件实验与冷启动复现均通过；
- 当前任何章节都不得把上游论文结果写成本书实测结果。

## 许可证

本仓库中的原创正文、图表、教学材料和代码采用 [MIT License](LICENSE)。第三方代码、数据、模型、论文和图片仍遵循各自的许可证与使用条款。
