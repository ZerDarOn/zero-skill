# Relationship overcorrection regression 08

这是 `relationship-review` 0.1.3 的独立前向回归，检查第十五轮新增规则是否会在信息已经充分时过度追问、在普通邀约中套用防御性停止条件，或只能复现先前题面。

六个未进入 active 登记的合成任务覆盖：发言人与安排都清楚的一句话确认、已经按消息编号给出身份映射、用户明确不要追问并要求条件分支、门禁卡交接争议、明确双向邀约，以及拒绝原时间但给出具体替代时间。前三类重点检查身份规则的适用边界，后两类检查反操控和停止追问规则不会污染正常协调；门禁卡任务只检查来源归属规则在相近交接争议中的回归表现，不单独支撑跨领域泛化结论。

无 Skill 与0.1.3使用相同的 `gpt-5.6-sol` medium、任务正文和只读隔离环境。Skill臂采用项目级显式调用；硬标准不进入生成提示。六题、两臂各重复三次，共36个独立输出，失败不重试。

正式运行前须由另一个同项目任务检查题面是否已经给出身份、条件分支是否可执行、负向标准是否把合理回复误判为过度纠正。冻结后先提交再运行。评分时隐藏候选映射，并保留模型评阅和显式加载的限制。

本实验不测试隐式发现，不新增第三方上游，也不使用真实聊天、账户或人物材料。

准备命令：

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/relationship-overcorrection-regression-08/promptfoo.json
```

运行、汇总与盲评沿用 [`evaluations/promptfoo/README.md`](../../promptfoo/README.md)。
