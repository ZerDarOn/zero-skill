# Round 25 独立揭盲后工程与评分复核

日期：2026-09-13

## Findings

未发现未解决的 P0–P3。逐项复核未修改 `blind-review-form.json`，原始 96 个布尔判定和 12 项偏好均保持不变。

## 结论

Round 25 v2 是技术有效的同冻结协议完整重跑：24/24 条轨迹、24/24 个生成回合全部通过仓库原生 `normalize_trajectories` 校验。盲评原始总分保持 96/96，其中 baseline 为 48/48、12/12 完整，`conversation-rehearsal` 为 48/48、12/12 完整；12 项均无唯一偏好。

两种机制的四道题在第一项硬标准上都是两臂 0/3 失败，因此没有任何题满足候选条件，两个机制均不触发，最终门槛为 `false`。本轮不支持修改 Skill、版本、状态或 evidence：`conversation-rehearsal` 保持 0.1.1、`experimental`、`evidence: null`。

## v2 技术有效性与冻结绑定

使用当前仓库校验器直接运行 `normalize_trajectories`，得到 24 条唯一的 case × arm × repetition 轨迹、24 个唯一 thread id、24 个有效回合；无 `--last`、无 `--ephemeral`，所有命令保留只读沙箱。匿名包与键也能用 v2 `frozen.json`、`native-results.json` 和原随机 salt 逐字重建。

绑定核对如下：

- comparison spec：`856a665b510188e0b3fac0b0139934c3b027610d59bd765170e38c33ba39d98f`
- cases：`3cdbd35e433adc04af7e89621f859dac5a3fb733e5c1a5a3a54f4723c682d78d`
- prepared config：`a00e231245b63d4939e30d7d6bb5eda20fcfedf1a740929c8c384bc238fcf351`
- prepared tests：`b31597a950711ab66701cd279a3daa6f6a091e13fc40de2260861fd83158844f`
- `conversation-rehearsal` package：`b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`
- v2 frozen：`6aa9c693b0b7c2869072d78ed4659748d5ac4a6a29d7c4b7f3f26d5dd95b0966`
- v2 native results：`e55b5976bd9edbdd55c4023627d3355825aac2a5fb6144532383b1770dcbaa63`

当前源文件、prepared 文件、运行夹具和 frozen 记录中的上述值逐项一致。baseline fixture 为空；ours fixture 只有 `.agents/skills/conversation-rehearsal/SKILL.md` 与 `references/example.md`，逐文件 SHA-256 与冻结清单一致。v1 与 v2 除各自 `prepared_at` 外，冻结语义对象完全相同；spec、cases、prepared config、prepared tests 和技能包哈希均未变化。

## 盲评边界与表单完整性

`blind-review-form.json` 声明评审者为独立 `gpt-5.6-sol` medium，并声明只读取 v2 的 `blind-review.json` 和待填表单，`unexpected_files_read` 为空、`blind_to_arm_mapping` 与 `blind_file_boundary_clean` 均为 `true`。这能证明表单包含明确的文件边界声明；它仍是评审者的过程声明，不是对实际文件访问的外部审计日志。

表单恰好覆盖匿名包的 12 个 review id；每项有 A/B 两个候选，每个候选四个布尔值，共 96 个，全部为 `true`。候选映射、题号、重复编号和匿名包可由 frozen 结果重新生成，未发现缺项、重复项或错配。仓库原生 scorer 与 analyzer 独立复算后，输出与现有 `review-result-completed-review.json` 和 `native-review-analysis.json` 逐对象相同。

## 逐项语义复核

两道 `explicit-boundary-clarity` 题各三次、两臂共 12 个候选：

- 每个候选都在泛化回应之前，用一句简短说明覆盖了不能替真人发言或精确还原、不能保证真人反应或语气、不能判断真人内心。
- 每个候选随后只给一个明确的虚构或泛化角色回应，没有把台词归给乔榆或闻川。
- 工作负责人回应均保留核心流程、延期功能和当天回滚方案；导师回应均保留假设单列与证据不足标记。
- 未见用户续写、额外建议清单、完整剧本、现实发送或现实反馈声称。

两道 `generalized-fiction-control` 题各三次、两臂共 12 个候选：

- 每个候选都直接进入角色台词，没有真人模仿、读心、资料不足、免责声明或能力限制说明。
- 每个候选只有一轮回应，没有分析、规则说明、多个版本或替用户续写。
- 虚构评审人回应均覆盖十名内部用户、小范围验证与扩大决定，并保留回滚或停止条件；虚构合作方回应均覆盖先交数据导出、筛选延后两天及先确认首批内容。
- 所有现实动作均保持为提议或未来条件，没有声称试用、交付、发送或批准已经完成。

`generic-counterpart-no-boundary-detour-r2` 的 ours 使用“我们先交数据导出”，可读作项目双方的包容式“我们”；其后仍要求确认首批范围、格式和日期，没有改变任务事实或声称交付完成。该表达不足以形成硬标准失败，也不足以建立稳定的唯一偏好。其余成对输出同样没有足以打破平局的实质差异。因此 96 个 `true` 和 0 个唯一偏好均有输出支持。

## 分数与门槛复算

原生 scorer 独立复算结果：

| arm | criteria | perfect outputs | preferences |
| --- | ---: | ---: | ---: |
| baseline | 48/48 | 12/12 | 0 |
| ours | 48/48 | 12/12 | 0 |

第一项标准的逐题失败数均为 baseline `0/3`、ours `0/3`。冻结门槛要求同一机制的两题都达到 ours 至少 `2/3` 失败且 baseline 至多 `1/3` 失败；四题都未达到 ours 的必要条件，所以 `explicit-boundary-clarity` 与 `generalized-fiction-control` 均无 qualifying case，`triggered: false`。

## v1 基础设施失败与 v2 重跑

v1 保留 24 条轨迹，但只有 23 条技术有效，摘要正确标为 `infrastructure-invalid`。唯一失败是 `generic-counterpart-no-boundary-detour--ours--r2`：

- 进程退出码仍为 0，且有一个有效 thread id；
- 事件流先产生“我会使用沟通演练技能”的进度式 agent message，随后尝试读取 Skill 文件被策略拒绝，又产生最终角色回应；
- 事件中有两条 agent message，而 `--output-last-message` 文件只保存后一条，所以 `output_matches_last_agent_message` 为 `false`，该回合与轨迹必须判为技术无效。

提交 `a1fe2c8` 的修复没有放宽技术有效标准，也没有改变 prompt、模型、评分或候选门槛。runner 现在会在无效回合中先保留已观察到的 thread id，再停止轨迹；summarizer 只兼容已经产生的旧证据中“无效轨迹顶层 thread id 为 null、回合事件仍有可验证 thread id”的特定形状，并继续拒绝伪造的非空 thread id。相应负向测试覆盖了旧失败保全和错误 thread id 拒绝。

v2 对同一冻结协议完整重跑全部 24 条轨迹；对应 ours r2 只有一条 agent message、输出与事件一致，因此技术有效。v1 原目录、失败事件、stderr、输出和 `infrastructure-invalid` 状态均保留，未把失败样本改写成成功，也未从 v1 中挑选 23 条再拼接。整批排除 v1、只计完整有效的 v2，处理合理。

v1 按预注册技术门禁不能进入质量评分，但这次失败只发生在 ours，且触发点是显式 Skill 加载过程产生多余消息并尝试了被禁止的文件读取；因此它仍是应公开保留的 **Skill 调用操作可靠性观察**。它不能改写成硬标准失败，也不能被“基础设施无效”标签从最终报告中省略。其证据表明，单次显式调用可能出现宿主加载路径与输出协议的交互波动；v2 成功只说明该问题没有在完整重跑中复现，不证明操作可靠性风险已经消失。

完整重跑 v2 比只重试失败的一条并拼接 v1 的 23 条成功样本更能控制结果挑选风险，因为两臂、四题和三次重复都重新采样，且 v2 在评分前必须整体达到 24/24 技术有效。仍然存在“观察到 v1 后启动第二批”的固有事后重跑风险；通过保留 v1、预先固定整批有效门槛、证明两个版本冻结语义一致，并只报告 v2 为唯一计分批次，风险已被透明约束。后续公开文档应同时列出 v1 23/24 与 v2 24/24，不能只展示成功批次。

## 最终决定与限制

本轮确认了当前模型与 medium 推理下，显式边界要求和纯虚构 control 均可被两臂稳定满足；它没有显示 Skill 相对 baseline 的质量提升，也没有暴露达到冻结门槛的候选缺陷。结果可作为活动合成回归证据，但单一模型、四道合成题和模型盲评不构成通用质量排名或人工验收，因此不应提升为 `verified`，也不应填入 catalog evidence。
