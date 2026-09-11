# Relationship boundary regression 05

这是 `relationship-review` 0.1.1 对无 Skill 的第二层泛化回归。上一轮六题单次三臂 pilot 中，本地 Skill 与基线都为 19/19，说明基础题出现天花板；本轮使用六个未进入 active 登记的更难组合任务，每题重复三次，检查来源冲突、未知身份和明确边界的升级变体，以及操控请求与家庭边界。

覆盖范围：口头通知争议下的一句话修复、发言人和用户位置都未知的转写、以制造嫉妒为目标的请求、家庭关系中的固定视频要求、借共同朋友绕过明确停止联系，以及第三方转述与本人否认。任务材料全部合成，不使用真实聊天、账户或人物。

两臂使用相同的 `gpt-5.6-sol` medium、任务正文和只读隔离环境。Skill 臂采用项目级显式调用；硬标准只进入运行后的匿名评分包，不进入生成提示。正式计划为 6 题 × 2 臂 × 3 次，共 36 个独立输出，模型输出失败不重试。三次重复只检查这六个合成题的会话内稳定性，不把 36 个输出当作 36 个独立任务，也不支持现实关系建议的一般质量结论。

运行前由另一个同项目任务只读复核题面与标准，重点排除隐藏要求、实现绑定、重复题和无法语义判断的长度条件。冻结后先提交再运行。结果须逐项盲评并保存评分表，之后才打开映射 key。

本实验不测试隐式发现；当前宿主的成功 `SKILL.md` 读取轨迹门禁仍未通过。上一轮 LoveHelper 已暴露阶段分数与进攻性话术风险，本轮只检查本地 Skill 在这六题中是否相对强基线更少出错，不重复第三臂。

准备命令：

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/relationship-boundary-regression-05/promptfoo.json
```

运行、汇总与盲评沿用 [`evaluations/promptfoo/README.md`](../../promptfoo/README.md)。
