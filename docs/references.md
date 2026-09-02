# 核心参考文献与一手资料

本页为读者提供按知识主线组织的继续阅读入口，不是正文全部链接的机械汇总。正文中的固定 commit、具体源码文件和版本化文档用于支撑局部实现判断，仍保留在相应段落；这里优先收录奠定概念、方法或评测原则的论文、课程、标准与官方项目。

## 怎样理解本书的引用

- 论文支持的是其研究问题、设定和报告范围，不自动支持其他平台或任务上的同名结论；
- 官方仓库和文档可以说明特定版本的接口与发布状态，不自动证明方法效果；
- 课程和教材用于建立稳定概念，不替代针对具体系统的实验或安全验证；
- 标准和规范定义接口或流程要求，不等于系统已经满足这些要求；
- 本书的解释、分类和建议仍是本书的综合判断，不应转写成来源作者的原话。

正文使用 `[P]`、`[A]`、`[O]` 和 `R0`–`R4` 区分来源与复现状态。它们描述“我们掌握了什么证据”，不是对论文或项目质量的排名。

本页采用“作者或机构，标题，出版物/项目，年份”的统一顺序；官方仓库作为实现入口单列，不与论文合并成同一证据。网页会持续更新时，正文仍以具名版本或固定 commit 为准。本页是精选阅读书目，不追求覆盖正文每一个链接。

## 第一部分：从视觉到闭环

### 第1章 从“看见”到“行动”

- Ross, Gordon, and Bagnell, [DAgger: A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://arxiv.org/abs/1011.0686).
- Lynch and Park, [Modern Robotics](https://modernrobotics.northwestern.edu/).
- Sutton and Barto, [Reinforcement Learning: An Introduction, Second Edition](http://incompleteideas.net/book/the-book-2nd.html).
- MIT, [Underactuated Robotics: Output Feedback](https://underactuated.mit.edu/output_feedback.html).

### 第2章 世界模型到底是什么

- Gelada et al., [DeepMDP: Learning Continuous Latent Space Models for Representation Learning](https://proceedings.mlr.press/v97/gelada19a.html).
- Grimm et al., [The Value Equivalence Principle for Model-Based Reinforcement Learning](https://arxiv.org/abs/2011.03506).
- Meta AI, [V-JEPA 2](https://github.com/facebookresearch/vjepa2), 作为预测表征与动作接口的边界案例。

### 第3章 最小机器人学与决策基础

- Lynch and Park, [Modern Robotics](https://modernrobotics.northwestern.edu/nu-gm-book-resource/).
- MIT, [Robotic Manipulation: Perception, Planning, and Control](https://manipulation.mit.edu/).
- ROS, [REP-103: Standard Units of Measure and Coordinate Conventions](https://www.ros.org/reps/rep-0103.html).
- ROS, [REP-105: Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html).

### 第4章 数据、基线与实验协议

- Gymnasium, [Handling Time Limits](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/).
- Hugging Face, [LeRobot Dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3).
- Agarwal et al., [Deep Reinforcement Learning at the Edge of the Statistical Precipice](https://arxiv.org/abs/2108.13264).

## 第二部分：世界模型基础

### 第5章 生成式基础

- Kingma and Welling, [Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114).
- van den Oord, Vinyals, and Kavukcuoglu, [Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937).
- Ho, Jain, and Abbeel, [Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239).
- Lipman et al., [Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747).
- Lakshminarayanan, Pritzel, and Blundell, [Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles](https://proceedings.neurips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html).

### 第6章 循环状态空间模型

- Ha and Schmidhuber, [World Models](https://arxiv.org/abs/1803.10122).
- Hafner et al., [Learning Latent Dynamics for Planning from Pixels](https://proceedings.mlr.press/v97/hafner19a.html).
- Hafner et al., [Dream to Control: Learning Behaviors by Latent Imagination](https://arxiv.org/abs/1912.01603).

### 第7章 用模型做规划

- Hafner et al., [PlaNet](https://proceedings.mlr.press/v97/hafner19a.html).
- Schrittwieser et al., [MuZero official overview](https://deepmind.google/blog/muzero-mastering-go-chess-shogi-and-atari-without-rules/).
- Hansen, Wang, and Su, [TD-MPC2 official repository](https://github.com/nicklashansen/tdmpc2).
- Chua et al., [Deep Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics Models](https://papers.nips.cc/paper_files/paper/2018/file/3de568f8597b94bda53149c7d7f5958c-Paper.pdf).

### 第8章 在想象中学习

- Hafner et al., [Dream to Control](https://arxiv.org/abs/1912.01603).
- Hafner et al., [Mastering Atari with Discrete World Models](https://arxiv.org/abs/2010.02193).
- Pardo et al., [Time Limits in Reinforcement Learning](https://proceedings.mlr.press/v80/pardo18a.html).

### 第9章 世界模型评测

- Gneiting and Raftery, [Strictly Proper Scoring Rules, Prediction, and Estimation](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).
- Guo et al., [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html).
- [How Should World Models Be Evaluated?](https://arxiv.org/abs/2606.15032).
- [WorldArena 2.0](https://arxiv.org/abs/2605.17912).

## 第三部分：预测表征与可行动空间

### 第10章 JEPA 与预测表征

- Assran et al., [Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture](https://arxiv.org/abs/2301.08243).
- Bardes et al., [V-JEPA](https://arxiv.org/abs/2404.08471).
- [V-JEPA 2](https://arxiv.org/abs/2506.09985).

### 第11章 动作条件视频

- Alonso et al., [DIAMOND official repository](https://github.com/eloialonso/diamond).
- Valevski et al., [GameNGen](https://gamengen.github.io/).
- NVIDIA, [Cosmos Predict](https://github.com/nvidia-cosmos/cosmos-predict2.5).

### 第12章 可行动空间表征

- Tian et al., [Occ3D](https://arxiv.org/abs/2304.14365).
- Wang et al., [OpenOccupancy](https://arxiv.org/abs/2303.03991).
- [OpenScene official repository](https://github.com/OpenDriveLab/OpenScene).
- [Nerfstudio official repository](https://github.com/nerfstudio-project/nerfstudio).

## 第四部分：动作策略与规模化

### 第13章 模仿学习与动作分块

- Ross, Gordon, and Bagnell, [DAgger](https://proceedings.mlr.press/v15/ross11a.html).
- Zhao et al., [Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://arxiv.org/abs/2304.13705).
- Hugging Face, [LeRobot](https://github.com/huggingface/lerobot).

### 第14章 生成式动作

- Chi et al., [Diffusion Policy](https://diffusion-policy.cs.columbia.edu/).
- Lipman et al., [Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747).
- Physical Intelligence, [openpi](https://github.com/Physical-Intelligence/openpi).

### 第15章 VLA 架构模式

- Brohan et al., [RT-2](https://arxiv.org/abs/2307.15818).
- Kim et al., [OpenVLA](https://github.com/openvla/openvla).
- [FAST](https://arxiv.org/abs/2501.09747).
- Shukor et al., [SmolVLA](https://arxiv.org/abs/2506.01844).

### 第16章 数据规模化与跨本体迁移

- Google DeepMind, [Open X-Embodiment](https://github.com/google-deepmind/open_x_embodiment).
- Khazatsky et al., [DROID](https://droid-dataset.github.io/).
- [Octo official repository](https://github.com/octo-models/octo).
- AgiBot, [AGIBOT WORLD 2026](https://agibot-world.com/), 2026.
- X-Humanoid, [RoboMIND 2.0](https://log2r.github.io/RoboMIND2.0/), 2026.
- FlagOpen, [RoboCOIN](https://FlagOpen.github.io/RoboCOIN/), 2025.

## 第五部分：世界模型与策略融合

### 第17章 世界模型怎样帮助策略

- [V-JEPA 2](https://arxiv.org/abs/2506.09985), 作为表征预训练路线。
- [DreamerV3](https://github.com/danijar/dreamerv3), 作为学习环境与策略优化路线。
- NVIDIA, [Cosmos Predict](https://github.com/nvidia-cosmos/cosmos-predict2.5), 作为动作条件未来生成路线。

### 第18章 VLA 后训练与 World-Action Models

- [RIPT-VLA](https://arxiv.org/abs/2505.17016).
- [VLA-RFT](https://arxiv.org/abs/2510.00406).
- [World-Gymnast](https://arxiv.org/abs/2602.02454).
- Luo et al., [HIL-SERL: Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning](https://hil-serl.github.io/), 2024.

## 第六部分：仿真、评测与部署

### 第19章 物理仿真与 Sim2Real

- NIST, [Verification, Validation, and Uncertainty Quantification Procedures](https://www.nist.gov/publications/summary-industrial-verification-validation-and-uncertainty-quantification-procedures).
- Google DeepMind, [MuJoCo](https://github.com/google-deepmind/mujoco).
- [MetaDrive](https://github.com/metadriverse/metadrive).
- [CARLA](https://github.com/carla-simulator/carla).

### 第20章 具身评测

- Hanley and Lippman-Hand, [If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators](https://pubmed.ncbi.nlm.nih.gov/6827763/).
- [LIBERO official repository](https://github.com/Lifelong-Robot-Learning/LIBERO).
- [SimplerEnv official repository](https://github.com/simpler-env/SimplerEnv).
- Field and Welsh, [Bootstrapping Clustered Data](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x).

### 第21章 部署、实时性与安全边界

- ROS 2, [Actions design](https://design.ros2.org/articles/actions.html).
- AUTOSAR, [E2E Protocol Specification R25-11](https://www.autosar.org/fileadmin/standards/R25-11/FO/AUTOSAR_FO_PRS_E2EProtocol.pdf).
- Autoware, [Velocity Smoother](https://autowarefoundation.github.io/autoware_core/main/planning/autoware_velocity_smoother/).
- Hugging Face, [LeRobot asynchronous inference](https://github.com/huggingface/lerobot/blob/128d3324e3202ce1fca1340fb8d7941edecce9d3/docs/source/async.mdx).

## 第七部分：综合研究闭环

### 第22章 综合论证

- ACM, [Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
- SLSA, [Provenance specification](https://slsa.dev/spec/v1.2/provenance).
- Research Object, [RO-Crate specification](https://www.researchobject.org/ro-crate/specification/1.2/introduction.html).
- NeurIPS, [Reproducibility checklist](https://blog.neurips.cc/2021/03/26/introducing-the-neurips-2021-paper-checklist/).

## 使用与维护原则

优先从本页理解一个领域的基础脉络，再回到正文查看具体论断所对应的版本化证据。新增文献必须说明它补足了哪个概念缺口或改变了哪项判断；仅因更新、热门或模型规模更大，不足以进入核心参考文献。

链接失效不等于来源失效。维护时应先寻找同一论文的出版页、作者页面或官方归档，再决定是否替换；不得用二手摘要替代原始来源，也不得在没有重新核对正文的情况下把新版本结论套用到旧版本描述。
