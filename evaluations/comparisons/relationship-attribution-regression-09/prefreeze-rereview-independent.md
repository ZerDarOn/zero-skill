# Independent pre-freeze rereview

- reviewer: `gpt-5.6-sol` medium
- date: 2026-09-11
- decision: **可冻结**

## Previous findings

### 已关闭：更正后已相容的说法被要求显式复述

- case: `corrected-draft-not-sent`
- location: `cases.json:23-29`
- resolution: purpose 已收窄为采用最新更正且不把责任推回对方。第二项标准现在只禁止把 B 未收到无依据归因于 B 漏看、系统吞信或其他原因，并明确在 A 已确认没有发送后不要求机械重复来源标签。自然的“承认此前说错、说明草稿未发、立即补发并确认”可以公平通过。

### 已关闭：候选规则与三个新题一一枚举

- location: `skills/relationships/relationship-review/SKILL.md:33`
- resolution: 规则已删除三类题目的逐项枚举和具体失败过渡语，统一抽象为来源链、证明范围、当前有效状态与真实证据层级。当前措辞仍明确输出形状无关、行动不能挤掉责任相关来源、不能只保留用户一方，但没有嵌入本协议三个题目的分类答案。

## New findings

无新的阻断项。

## Rereview checks

- `nested-handoff-report-chain`：A 的记忆、B 的亲历和 B 对 C 不确定说法的转述层级完整；三项标准均可从输出直接判断。
- `partial-system-record-invitation`：系统记录的有限证明范围、双方说法与补救动作边界完整；标准没有把会议创建误当成邀请送达。
- `corrected-draft-not-sent`：先前说法、最新更正、B 未收到和 A 的修复责任逻辑一致；修订后不会因省略冗余来源标签误判合理回复。
- 候选规则仍受“涉及争议经过”和“影响责任判断”约束，没有扩大到明确邀约、既定安排或普通无争议回复。
- 六个反过度纠正旧题的 prompt、purpose 和 hard criteria 保持原样，可继续检查身份追问、条件分支、正常邀约、替代时间及门禁卡近邻回归。
- baseline、冻结0.1.3和0.1.4候选共享模型、reasoning effort、任务正文、重复次数及只读约束；两个Skill臂均为项目级显式调用，唯一预期差异是技能包版本。
- hard criteria 未进入 `common_prompt` 或任务正文；未发现候选映射、理想措辞或评分标准泄漏。
- 九题、三臂、三次重复，总计划为 `9 x 3 x 3 = 81` 个输出。
- README 对合成材料、显式加载、模型盲评、非独立人工评审、无隐式发现、失败不重试及升版门槛的限制表述准确。

## Conclusion

两个原发现均已关闭，没有新阻断项，**可以冻结**。冻结后应先提交再运行，并保留既定门槛：只有0.1.4候选在三个新证据拓扑上稳定改善来源保留，且六个复用题相对0.1.3不退化，才正式更新目录版本。
