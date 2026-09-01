# EXP-14-01：双峰动作与采样预算 smoke

同一观测下有 `-1` 与 `+1` 两个等权有效动作。实验比较条件均值、迭代 mode-refinement 接口和已知配对的 oracle straight-flow 路径，报告到有效模式的距离、无效率、模式覆盖与 sample-model evaluation。它还对比同样覆盖两个模式且全部有效的 `5:5` 与 `9:1` 样本，检查模式覆盖无法识别频率失真；随后显式区分候选数、solver 步数、batch 容量和顺序 forward，用边际接受率同为20%的 iid/完全相关解析端点检查 best-of-N 联合相关性假设，并用手工阻塞区验证“接近数据模式”不等于“当前场景允许执行”。

```bash
make ch14-test-local
make ch14-smoke-local
make ch14-smoke
```

mode-refinement 不是 DDPM，oracle flow 已知目标配对，10个手工样本也不能估计总体概率校准；20%概率和两种依赖结构是解析端点，安全门更不是碰撞器。实验只验证多峰动作、频率诊断、候选相关性、采样预算和筛选合同，不是 Push-T、Diffusion Policy、π0 或实时性能。代码和 fixture 按仓库 MIT 许可发布。
