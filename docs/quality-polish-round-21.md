# 第二十一轮质量打磨：人物证据自然语境前向诊断

日期：2026-09-13

## 范围

第八轮的六题单次 pilot 中，`person-evidence-analysis` 0.1.2 严格得分为22/24、4/6完整，无 Skill 为20/24、3/6完整；随后四题平衡证据复查的语义核心分两臂同为16/16。一次共同遗漏没有稳定复现，但单次运行不足以判断自然语境中的来源层级、行动角色和有限模式。

本轮在运行前冻结六个全新合成表面：人物自述原因与后续行动、主管标签与不同情境下的决定、事故建议与最终责任、地点选择与持续组织、带紧急例外的有限互动模式、严格两句话中的第三方标签与直接反证。每题四项硬标准，每臂重复三次，共36份输出、144个布尔判断。

冻结前独立复核发现两个阻塞问题：行动角色核心项混入过多次要细节，可能把细节遗漏误算成角色错误；自述题又要求精确复述 `14:10`，重复了第八轮的过严标准。协议拆分并放宽这两处后，二次复核通过。冻结提交为 `359ef9533d8a7bc316e38659f53b18db10df5e9c`，0.1.2包指纹为 `bf74c8e3288c5f5a3ca751235815089731aeed0ef3ee92b74e396251c93a33ef`。

无 Skill 与0.1.2使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读隔离环境。36份输出全部有效，没有 provider error、禁止工具调用、失败重试或排除。

## 结果

| 实验臂 | 标准通过 | 完整输出 | 偏好 | 总 token | 中位延迟 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无 Skill | 67/72 | 13/18 | 3 | 175,515 | 8,365 ms |
| 0.1.2 | 70/72 | 16/18 | 5 | 199,884 | 10,198 ms |

另有10次持平。逐题结果为：

| 用例 | 无 Skill | 0.1.2 | 核心错误：无 Skill / 0.1.2 | 偏好：无 Skill / 0.1.2 |
| --- | ---: | ---: | ---: | ---: |
| 自述原因与后续行动 | 12/12，3/3完整 | 12/12，3/3完整 | 0/3 / 0/3 | 0 / 1 |
| 主管标签与不同决定 | 12/12，3/3完整 | 12/12，3/3完整 | 0/3 / 0/3 | 2 / 0 |
| 事故建议与最终责任 | 12/12，3/3完整 | 12/12，3/3完整 | 0/3 / 0/3 | 0 / 0 |
| 地点选择与持续组织 | 9/12，0/3完整 | 10/12，1/3完整 | 0/3 / 0/3 | 0 / 2 |
| 带紧急例外的有限模式 | 12/12，3/3完整 | 12/12，3/3完整 | 0/3 / 0/3 | 1 / 0 |
| 两句话中的来源与反证 | 10/12，1/3完整 | 12/12，3/3完整 | 2/3 / 0/3 | 0 / 2 |

0.1.2的两项失败都在地点题的第一项：两次回答保留了阿锐的地点选择角色，但没有写出选择结果是“东门”。角色核心项是第二项，两臂三次都通过，因此不能把该细节遗漏解释为行动责任退化。无 Skill 的五项失败包含相同地点细节三次，以及严格两句题中两次没有把同事评价明确标成无具体事例的第三方概括；后者属于来源层级核心失败。

本轮 `summary.json` 在盲评前生成，状态为 `awaiting-human-review`，只证明运行和基础设施完整。正式质量分来自匿名评阅、冻结后的候选映射和评分器结果，不能用 Promptfoo 的执行通过行替代。

## 候选门槛与决定

冻结门槛要求：同一合格机制至少有两个不同题型，0.1.2在每题出现不少于 `2/3` 核心错误，同时 baseline 在对应每题不超过 `1/3`。来源层级三题中，0.1.2核心错误依次为0、0、0；行动角色两题为0、0。有限模式只有一个题型，协议预先规定只作诊断，不能单独触发候选。

门槛未触发。保持 `person-evidence-analysis` 0.1.2，不修改 Skill、不设计0.1.3、不升版，状态仍为 `experimental`，`evidence` 仍为 `null`。六题全部加入活动回归，人物分析用例从10项增至16项，全仓活动用例从119项增至125项。地点结果的两次非核心遗漏作为后续回归信号保留。

## 盲评过程

独立 Codex 任务收到随机化的 A/B 候选，在评分时没有读取候选映射或分数；完成文件先锁定为 SHA-256 `7dcc6fd4c069367170da20c1663f445c0b8c0aa3a0ff1ca4ca541a917ed092dc`，之后才解盲计分。评阅者此前看过本轮协议和当前技能版本，因此不是对方法完全无先验的评审。

评阅任务随后主动更正过程披露：评分前还读取了全局通用的 `$CODEX_HOME/skills/repo-conventions/SKILL.md`，超出“只读两份匿名文件”的字面边界。该文件不含本轮协议、候选身份、分数或人物分析技能内容，候选到实验臂的映射仍未泄漏，所以本报告保留“内容盲”结果；同时明确标记 `file_access_boundary_clean: false`，不声称实现了绝对文件访问隔离。

## 成本与边界

0.1.2总 token 多24,369，约13.9%；prompt token约多13.1%，completion token约多70.7%；记录成本约高31.4%，中位延迟约高21.9%。这里只有一次实验运行，没有调用顺序平衡或置信区间，不能把成本与延迟差解释为稳定性能结论。

- 全部材料为合成数据；
- 单模型、单推理等级、每臂18份输出；
- 使用项目级显式调用，隐式路由没有重测；
- 评阅者是模型辅助匿名评审，不是独立人类领域评审；
- 评阅者有协议与技能先验，并发生一项不含身份信息的文件访问边界偏差；
- 严格两句与格式约束同时测试指令遵循和人物证据推理；
- 未测试真实聊天、长期人物建模、其他模型或生产使用，不能据此标记 `verified` 或宣称普遍优越。

## 校验

- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：74项中73项通过，1项因 Windows 无符号链接权限跳过；
- 第21轮三项专用测试覆盖分数与门槛复算、冻结案例镜像，以及来源、标准、输出、评分和流程披露的负向变异。

材料：

- [冻结协议](../evaluations/comparisons/person-evidence-natural-context-forward-14/README.md)
- [首次冻结前复核](../evaluations/comparisons/person-evidence-natural-context-forward-14/prefreeze-review-independent.md)
- [修订后二次复核](../evaluations/comparisons/person-evidence-natural-context-forward-14/prefreeze-rereview-independent.md)
- [独立揭盲后决策](../evaluations/comparisons/person-evidence-natural-context-forward-14/postscore-decision-review-independent.md)
- [首次最终工程复核与发现](../evaluations/comparisons/person-evidence-natural-context-forward-14/final-engineering-review-independent.md)
- [修复后的最终工程复审](../evaluations/comparisons/person-evidence-natural-context-forward-14/final-engineering-rereview-independent.md)
- [自包含机器诊断](../evaluations/reports/person-evidence-natural-context-round-21-diagnostic.json)
- [当前人物证据分析 Skill](../skills/people/person-evidence-analysis/SKILL.md)
