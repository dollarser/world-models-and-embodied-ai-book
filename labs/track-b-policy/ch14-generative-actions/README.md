# EXP-14-01：双峰动作与采样预算 smoke

同一观测下有 `-1` 与 `+1` 两个等权有效动作。实验比较条件均值、迭代 mode-refinement 接口和已知配对的 oracle straight-flow 路径，报告到有效模式的距离、无效率、模式覆盖与模型调用数。

```bash
make ch14-test-local
make ch14-smoke-local
make ch14-smoke
```

mode-refinement 不是 DDPM，oracle flow 已知目标配对，也不是学习到的 flow policy。实验只验证多峰动作与采样/控制预算合同，不是 Push-T、Diffusion Policy 或 π0 性能。代码和 fixture 按仓库 MIT 许可发布。
