# Relationship boundary regression 06

第十五轮两臂泛化回归在三次重复中稳定暴露三个共同缺口：未知用户位置、口头通知争议的一句话来源保留，以及拒绝嫉妒策略后的停止追问条件。本协议在修订后冻结这三题，对比无 Skill、`relationship-review` 0.1.1 精确快照和候选 0.1.2。

三题、三臂各重复三次，共 27 个独立 `gpt-5.6-sol` medium 输出。三臂使用相同任务正文与只读隔离环境；Skill 臂采用原生项目级显式调用，硬标准不进入生成提示。输出在揭盲前由独立模型任务逐项评分，失败不重试。

0.1.1 快照是修改前包内两份文件的原始字节，保存在 `packages/relationship-review-0.1.1/`。候选臂从当前技能目录制作冻结运行快照。协议只验证这三个已观察缺口，不作为全领域质量、隐式发现或独立人工评审证据。

准备命令：

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/relationship-boundary-regression-06/promptfoo.json
```

运行、汇总与盲评沿用 [`evaluations/promptfoo/README.md`](../../promptfoo/README.md)。

## 结果

三臂各9个输出全部有效。冻结盲评分为无 Skill 12/27、0.1.1 12/27、0.1.2 23/27；完整输出分别为0/9、0/9、7/9，九次偏好全部给0.1.2。残留的无标签消息归并错误进入round-07，见[第十五轮报告](../../../docs/quality-polish-round-15.md)。
