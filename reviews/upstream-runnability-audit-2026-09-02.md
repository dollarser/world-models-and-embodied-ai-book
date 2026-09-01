# V-JEPA 2.1 与 Cosmos 3 上游可运行性边界审查

> 日期：2026-09-02  
> 范围：第10、11、17章与研究雷达中的两个快速演进开源锚点  
> 结论：修正“公开资产存在”到“默认路径可执行”之间的证据越级；未下载权重、数据或容器

## 1. 为什么要做源码级预检

论文、README、模型符号、checkpoint 链接和完整可运行命令是不同证据。此前正文正确地把 V-JEPA 2.1 与 Cosmos 3 标为 `[O,R1]`，但资源路线仍可能让读者误以为公开入口可以直接冷启动。本轮只用一手仓库 HEAD、锁定源码和许可证做无下载复核。

## 2. V-JEPA 2.1：符号与权重公开，默认 Hub 路径仍阻塞

`git ls-remote` 显示官方仓库 HEAD 仍为锁定的 `204698b45b3712590f06245fbfba32d3be539812`。该快照列有 `vjepa2_1_vit_base_384` 等模型符号，README 也给出 checkpoint 链接；但 `src/hub/backbones.py` 把公开下载基址注释掉，并把 `VJEPA_BASE_URL` 设为测试用 `http://localhost:8300`。因此普通新环境的 `torch.hub.load(..., pretrained=True)` 并不是当前可复核的冷启动路径。

正文据此保留 `[O,R1]`：部分公开资产可审计；不升级为 `R2`，也不在无 GPU 设备上下载或自造临时绕过。后续只有在锁定兼容 loader、显式 checkpoint URL、校验和、配置和容器后，才可执行 S1 微型推理。

## 3. Cosmos 3：Guardrail 与许可证都是实验合同

官方仓库 HEAD 仍为锁定的 `9aa98e5a0773a5558f07d2699e640858f7ca8827`。Action cookbook 明确区分 forward dynamics、inverse dynamics 和 policy 三个 mode；默认 Generator 路径要求申请 gated `Cosmos-1.0-Guardrail`，同时为 Diffusers、vLLM-Omni 和 Cosmos Framework 提供关闭 guardrail 的开关。

关闭 guardrail 会改变输入/输出安全处理，不能当成无语义差异的安装修复。任何后续实验必须记录开关、guardrail revision、授权状态和拒绝/模糊化行为。仓库根许可证为 OpenMDW-1.1；本书原创内容保持 MIT，但不能把 Cosmos 3、模型、数据、Guardrail 或依赖改写为 MIT，也不能沿用 Cosmos 2.5 的许可证描述。

## 4. 修订后的证据边界

- `R1` 只表示公开部分资产，不表示官方命令已在声明环境运行；
- 参数量和模型名不证明24 GB单卡可行；
- guarded 与 unguarded 运行不是同一安全配置；
- 本轮没有下载 checkpoint、申请访问、运行 GPU、仿真、机器人或车辆，因此没有新增性能结果；
- 第10章的 S1 保持 `blocked-by-upstream-loader`，但这不阻塞全书 CPU 主路径。

## 5. 验收

```text
make smoke-all
make docs-preview-check
make check
git diff --check
```

四项通过后，本轮才能作为来源准确性阶段提交。
