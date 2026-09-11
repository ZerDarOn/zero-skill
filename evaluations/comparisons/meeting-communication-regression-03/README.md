# Meeting communication regression 03

这是一组在生成前冻结的显式加载质量对照：`baseline` 与 `meeting-communication-review` 0.1.1 使用同一自然任务，唯一有意差异是 skill 臂的原生项目级安装与显式调用。7 个合成用例各重复 3 次，硬标准不会出现在模型提示中，结果需盲评后再揭示实验臂。

新题覆盖此前活动用例没有直接检验的边界：转述与否认、明确修订、主持角色造成的轮次占比、同名说话人归因、filler 计数与心理推断、转录缺口与一致同意、建议与已确认行动项。材料均为合成内容。

高星发现线索仍是 [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills/tree/be2a406907dbc61b73e6827ded415c96139d13a2/meeting-insights-analyzer)。2026-09-11 复核时仓库约 74,838 stars；固定提交没有根许可证，`meeting-insights-analyzer` 目录也没有单独许可证，所以本轮只比较设计取舍，不复制其文件或将其作为可发布实验臂。它的长处是任务模板、具体例子和可执行反馈结构；本地 skill 重点补强证据口径、未知状态、人物归因和有界输出。

准备命令：

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/meeting-communication-regression-03/promptfoo.json
```

运行、汇总与盲评沿用 `evaluations/promptfoo/README.md`。本实验不验证隐式发现，也不自动扫描、上传或分析真实会议材料。
