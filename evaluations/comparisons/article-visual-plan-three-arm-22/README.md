# Article visual plan three-arm 22

本轮比较无 Skill、`article-visual-plan` 0.1.0，以及 Baoyu Skills 固定提交 `6b7a2e417500561a5ecdd0b168332f4142584617` 的 `baoyu-article-illustrator`。目标是检查文本配图规划能否选择零张或一张真正有价值的图、保留证据强度，并在局部增删时维持计划状态。正式运行前不修改待测 Skill。

Baoyu 上游是包含偏好配置、确认、生图、文件写入和插图回填的端到端流程；本地 Skill 是窄范围的文本规划器。本轮只比较两者共同覆盖的规划子任务。公共提示明确跳过 `EXTEND.md`、首次设置、确认、生图、写盘和回填，并要求直接给最终计划；同一约束进入三臂。上游臂只提供上下文，不参与本地候选门槛；结果不能外推为两个完整产品的总排名。

## 固定上游

上游完整 `baoyu-article-illustrator` 目录按固定提交保留，包内只有 Markdown 指令、提示与引用。原文件、根 MIT 许可证、逐文件来源和 SHA-256 位于 `evaluations/fixtures/upstreams/baoyu-skills/6b7a2e417500561a5ecdd0b168332f4142584617/`。根许可证另按原字节复制到 Skill 包内，确保准备后的第三方实验包自带许可证。没有安装或运行上游代码，也没有把第三方内容登记为本地原创 Skill。

固定源的 `references/usage.md` 把 `references/style-presets.md` 写成相对于包根的样子；从该文件自身解析会落到不存在的二重 `references/references/` 路径，而实际目标文件已包含在包内。本夹具保留这个上游原貌并在 provenance 中记录，不静默修订第三方字节。六道题不要求读取命令语法或该链接，因而不依赖这个缺口。

## 六个前向任务

- `value-based-selection`：明确应为零张的反思周记；只有一个反馈循环值得配图但上限为三张的文章。
- `evidence-strength`：定性伴随关系与人手缺口；不同受访者和非标准提问下的定性方案比较。
- `plan-state-preservation`：在两个稳定 ID 之间新增一项；删除中间项同时保留剩余 ID 缺口和逐字内容。

每题四项硬标准，并在 `core_criteria` 中预先标明该机制的核心判断。题面不复用当前四个活动用例：选择题要求零张或唯一一张，证据题分别引入替代解释与不可直接排名的异组定性材料，状态题检查新增和删除而不是修订既有 V2。

## 规模与盲评

三臂使用相同的 `gpt-5.6-sol`、`medium`、只读隔离环境、公共提示和任务正文；两个 Skill 臂都采用项目级显式调用。每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个三候选匿名评阅项和 `54 × 4 = 216` 个布尔判断。失败保留且不重试。

评阅者在不知道臂映射的情况下逐项判断硬标准并记录偏好。数量、状态行和证据范围均按语义等价判断；不得用总体印象或偏好覆盖逐项标准。硬标准只判断最终文本中可观察的内容；是否真的调用工具、读写文件或发起生图由原始事件和运行有效性门禁判断。只有评分完成并锁定后才读取匿名映射。模型评阅属于独立模型辅助评阅，不等于独立人工视觉设计评审。

## 冻结候选门槛

本地改版门槛只比较 ours 与 baseline。对某一机制的两道题，若 ours 在每题都至少 `2/3` 次出现核心失败，同时 baseline 在每题最多 `1/3` 次核心失败，且 54 份输出全部满足运行有效性门禁，才打开最小候选设计。一次输出只要该题任一 `core_criteria` 为假即计为核心失败。upstream 仅帮助解释设计差异，不进入门槛。

门槛命中也只授权候选设计，不直接修改 Skill、升版或发布。单题失败、跨机制各失败一题、两臂共同失败、只在非核心标准失败、偏好差异或上游优劣都不能触发。冻结后不得改题、改标准或重跑失败来改变结论。

## 边界

本轮不测试隐式路由、实际图像质量、文字渲染、文件落盘、图片生成后端、编辑器集成或真实读者理解。当前 Windows 宿主的命令沙箱 provisioning 故障也意味着原始 provider items 中可观察到的 `command_execution`、`file_change`、MCP、网页搜索或 Codex app 调用都会使运行无效；公共任务本身不需要命令执行。若某次工具尝试在 provider item 形成前就被宿主拒绝，当前通用 Promptfoo 结果未必能证明该尝试发生，因此不宣称覆盖不可观察的预路由失败。

准备命令：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/article-visual-plan-three-arm-22/promptfoo.json
```

运行、汇总与盲评步骤见 [Promptfoo 评测说明](../../promptfoo/README.md)。
