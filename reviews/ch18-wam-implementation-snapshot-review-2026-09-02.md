# 第18章 WAM 实现快照审查

> 审查日期：2026-09-02
> 范围：第18章 World-Gymnast、WMPO、WAM taxonomy、SimWAM 实现证据与资源预检
> 结论：通过；实现来源、推断前提和资源执行边界已固定，完整门禁通过

## 发现

第18章按后训练信号和未来—动作接口分类的骨架合理，但数项实现级说明仍链接仓库首页。首页可以发现项目，却不能固定训练入口、attention mask、部署路径或资产体积；`CLAIM-18-05` 的推断证据也以浮动 SimWAM 首页作为前提。资源段还没有指出 World-Gymnast 上游脚本会清理宿主缓存并默认联网记录，这与本书的 Docker 优先、无授权外部写入原则不一致。

## 修改与证据

- World-Gymnast 锁定 `59c83a6e121fc1e099b39a4d6e01421cf1aa55c7`：README 固定 `partial_credit_criteria` 数据字段，训练脚本固定 OpenVLA-OFT 路径、`NUM_GPUS=4`、在线 W&B 与缓存清理行为；
- WMPO 锁定 `c836d74ec6f4525c93fe980d54d0ca870118615a`：README 分开 SFT policy、world model、VideoMAE reward model 与最终 policy，并标注完整 checkpoint/data 约 `364 GiB + 530 GiB`；
- WAM 教程锁定 `8ae8d6ad916728059559ae99417b8aacdaf22301`，只用其四类 taxonomy 作为本书接口分类的来源，不把分类名称当能力证明；
- SimWAM 锁定 `68b426c162827cb7701396895dbb3572d29f3420`：源码 mask 只开放 action→action 与 action→当前首帧 video token，README 描述不显式生成未来帧的直接轨迹预测；
- 新增 `CLAIM-18-09` 与事实证据登记；`CLAIM-18-05` 的 GitHub 推断锚点改为固定源码；新增正反规格测试，拒绝推断登记中的浮动 GitHub 首页。

## 资源、安全与证据边界

本阶段只读取固定 README、脚本和源码，没有执行任何上游 shell、删除缓存、登录 W&B、下载 checkpoint/data、安装依赖或运行 GPU。World-Gymnast 脚本若未来进入可选实验，必须先复制并最小化到一次性 Docker，关闭未授权遥测，显式挂载缓存并按本书最多双卡重新预检；不能把脚本默认四卡配置写成资源可行。WMPO 仍只允许清单级选择性预检，不允许整包默认下载。

SimWAM 的 mask 与 README 只能证明固定版本的代码接口和作者说明，不能证明视频分支带来因果收益、论文数字已复现、闭环道路安全或交互 simulator 能力。

## 门禁结果

- `make smoke-all`：通过，22 章共 308 个单元测试，22 组 smoke 均与登记结果一致；
- `make docs-preview-check`：通过，29 个 HTML、22 章、23 张可访问 Mermaid 图、116 个折叠式自检和 1161 个内部目标，附带 3 项生成站点语义测试；
- `make check`：通过，4 个 Schema、22 章、22 张实验卡、3 张 benchmark card 与 65 项严格规格测试通过；
- `git diff --check`：通过。
