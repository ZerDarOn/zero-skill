# Prose polish current Humanizer 24

当前 `prose-polish` 0.1.3 的严格复测集中在字符上限与关系保真；此前与 Humanizer 的三方比较使用的是本地 0.1.1。本轮用六个全新合成任务比较无 Skill、当前 0.1.3 和 Humanizer 3.0.0 固定提交，检查当前包相对 baseline 的重复退化机制，并描述与固定高星上游的差异。

Humanizer 固定在 `9862685f575c65a8247f90369951df1b3416e3d6`；2026-09-14 只读核对时该提交仍是远端 HEAD。原始 `SKILL.md`、`LICENSE`、UI metadata、逐文件 SHA-256 和无修改声明已经保存在 `evaluations/fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6/`。运行只加载其 Markdown 技能，不执行脚本，也不安装到全局目录。

## 六个前向任务

- `bounded-condition-preservation`：在 Unicode 字符上限内保留迁移范围、条件纳入、明确排除和计划不确定性，以及三个合取资格条件与例外。
- `revision-history-control`：以后续审计撤销旧指标但保留逐字主观引语；撤回局部人数更正而保留仍有效的条件性日期修订。
- `author-voice-restraint`：匹配克制样文但不移植其经历；对明确、刻意使用短句和重复的文本保持不改。

每题的硬标准只判断可核验的事实、关系、范围、字符数、受保护文字和是否新增材料。匿名评阅可以在所有硬标准之外记录自然度偏好；没有清楚差异时必须留空，偏好不进入候选改版门槛。

## 规模与门槛

三臂使用同一个 `gpt-5.6-sol`、medium、只读隔离配置、公共提示与任务正文；两个 Skill 臂采用项目级显式调用。每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个三候选匿名评阅项和 216 个布尔判断。失败保留且不重试。

本地候选门槛只比较 ours 与 baseline。对某一机制的两道题，若 ours 在每题都至少 `2/3` 次出现核心失败，同时 baseline 在每题最多 `1/3` 次核心失败，且 54 份输出全部满足运行有效性门禁，才打开最小候选设计。一次输出只要该题任一 `core_criteria` 为假即计为核心失败。upstream 只提供设计上下文，不进入门槛。

门槛只授权候选设计，不直接修改 Skill、升版或发布。单题失败、跨机制各失败一题、两臂共同失败、非核心差异、主观偏好或上游优劣都不能触发。冻结后不得改题、改标准或补跑失败来改变结论。

## 边界

本轮只测试单轮文本交付，不评价普遍文笔、作者身份、AI 检测规避、真实读者偏好、文件写入、发布、隐式路由或其他模型。Humanizer 的模式清单和本地 Skill 的完整能力也不会因六题结果形成总排名。模型辅助匿名评阅不等于独立人工编辑评审。

准备命令：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/prose-polish-current-humanizer-24/promptfoo.json
```

运行、汇总与盲评步骤见 [Promptfoo 评测说明](../../promptfoo/README.md)。
