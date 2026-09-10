# person-evidence-analysis 两组盲测 01

比较无 Skill 与当前 `person-evidence-analysis`。六个合成任务未参与 0.1.2 的规则编写，覆盖单次事件、重复转述、本人自述与行为冲突、时间变化、模糊指代，以及证据较充分时是否能给出有界模式。

本轮没有加入 [Nuwa 固定入口](https://github.com/alchaincyf/nuwa-skill/blob/fe0374687037c4cc51a65c1e0c145afe2981dc69/SKILL.md)：它的任务是调研并生成人物 Skill，不是分析用户已提供的人物片段。把不同任务的入口放进同题排名会把范围不匹配误写成质量差异。找到任务匹配且许可证可固定的上游后再增加第三组。

- 两组使用相同模型、推理等级和合成输入；本地 Skill 采用显式调用。
- 评分标准在生成前冻结，但不写入待测 prompt。
- 计划重复三次；先跑一次 pilot，查看是否有鉴别力和评分歧义。
- 摘要生成匿名候选与独立 key。评分时只打开 `blind-review.json`，保存布尔评分后再揭盲。
- 这不是自动路由评测；当前宿主的隐式读取链路仍未通过门禁。

实际 pilot 结果见[第八轮质量检查](../../../docs/quality-evaluation-round-08.md)与[脱敏诊断证据](../../reports/person-evidence-two-arm-01-pilot-diagnostic.json)。
