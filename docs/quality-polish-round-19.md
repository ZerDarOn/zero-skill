# 第十九轮质量打磨：定量保真前向诊断

日期：2026-09-11

## 范围

第十八轮中，`claim-evidence-review` 0.1.0 在共享数据题三次有两次没有同时保留两批精确数字，baseline三次有一次同类遗漏。本轮用四个新表面检查该风险是否跨题、跨重复稳定出现，运行前明确升版门槛，不修改Skill。

四题覆盖两个队列与共享复核、缺失分母且方向不一的地区材料、终点不同的两项随机试验，以及严格两条项目符号的跨产品压缩。无Skill与0.1.0使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读环境；每题每臂三次，共24个有效输出，没有provider error、禁止工具调用、失败重试或排除。

协议经独立复核后在提交 `704855f73c8b57ab595ebe1d89f54d09697f6e4e` 冻结。当前包指纹仍为 `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29`。

## 结果

| 实验臂 | 标准通过 | 完整输出 | 偏好 | 总 token | 中位延迟 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无Skill | 35/36 | 11/12 | 2 | 117,890 | 14,552.5 ms |
| 0.1.0 | 34/36 | 10/12 | 2 | 130,302 | 13,775.0 ms |

另有8次持平。0.1.0总token多12,412，约10.5%；completion token约多26.1%，记录成本约多38.7%，中位延迟约低5.3%。当前包没有硬分或偏好增益，较低中位延迟不足以抵消质量与成本结果。

逐题结果：

| 用例 | 无Skill | 0.1.0 | 偏好：无Skill / 0.1.0 |
| --- | ---: | ---: | ---: |
| 两项独立试验、不同终点 | 9/9，3/3完整 | 8/9，2/3完整 | 1 / 1 |
| 地区材料与缺失分母 | 8/9，2/3完整 | 8/9，2/3完整 | 1 / 1 |
| 两条跨产品摘要 | 9/9，3/3完整 | 9/9，3/3完整 | 0 / 0 |
| 两个队列与共享复核 | 9/9，3/3完整 | 9/9，3/3完整 | 0 / 0 |

当前包在试验题一次只给75%/65%和68%/64%，遗漏每组200人与250人的原始样本分母；在地区题一次保留了“前期分母缺失”，却漏掉仍已知的前期11单投诉。baseline也在地区题一次漏掉这11单。冻结协议与Skill正文都预先要求保留影响证据范围的分母和已知计数，所以不在揭盲后放宽标准。

## 决定

保持 `claim-evidence-review` 0.1.0，不修改Skill、不升版。本轮预声明要求：0.1.0至少在两个新题型中各自重复失败，且baseline在同题明显更少，才设计候选。当前版虽跨两个题型各失一次，却没有题型内重复；baseline也有同类地区题失败。34/36对35/36不能改写成稳定退化。

四题全部加入活动回归，`claim-evidence-review` 从10项增至14项，全仓活动用例从112项增至116项，状态仍为 `experimental`，`evidence` 仍为 `null`。

跨第十八、十九轮五个相关题型、每臂15个输出，0.1.0累计4次核心数字遗漏，baseline为2次。这个4对2是揭盲后的探索性风险汇总，只触发新的确认性协议：三个全新表面，每臂五次；只有当前版在至少两个题型各出现不少于2/5遗漏、baseline各不超过1/5，才打开0.1.1候选设计。

## 限制与校验

- 全部材料为合成数据；
- 单模型、单推理等级、每臂三次；
- 显式项目条件没有 `skillCalls` 遥测；
- 模型辅助匿名评审不是独立人工领域评审；
- 一分差、2比2偏好和跨轮4比2都不具统计显著含义；
- 隐式路由没有在本轮重测。

- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：69项中68项通过，1项因Windows无符号链接权限跳过。

材料：

- [冻结协议](../evaluations/comparisons/claim-quantitative-preservation-forward-12/README.md)
- [独立冻结前复核](../evaluations/comparisons/claim-quantitative-preservation-forward-12/prefreeze-review-independent.md)
- [独立揭盲后决策](../evaluations/comparisons/claim-quantitative-preservation-forward-12/postscore-decision-review-independent.md)
- [自包含机器诊断](../evaluations/reports/claim-quantitative-preservation-round-19-diagnostic.json)
- [当前论断证据审查Skill](../skills/research/claim-evidence-review/SKILL.md)
