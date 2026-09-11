# Relationship speaker mapping regression 07

0.1.2 在三次未知用户位置输出中都识别到身份缺失，但两次先把三条无标签消息归并成两个说话人，因此只完整通过一次。本协议使用一条新的四句合成对话，对比无 Skill、0.1.2 精确快照和候选 0.1.3，检查是否会直接询问逐句对应关系。

一题、三臂各重复三次，共 9 个独立 `gpt-5.6-sol` medium 输出。三臂共享任务正文和只读隔离环境；Skill 臂使用原生项目级显式调用，硬标准不进入生成提示。0.1.2 快照保存在 `packages/relationship-review-0.1.2/`。该定向实验只检查无标签消息映射，不证明全领域质量、隐式发现或独立人工评审。

准备命令：

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/relationship-speaker-mapping-regression-07/promptfoo.json
```

运行、汇总与盲评沿用 [`evaluations/promptfoo/README.md`](../../promptfoo/README.md)。
