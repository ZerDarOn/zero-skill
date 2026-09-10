# 第七轮评测校准：语义评分与隐式路由边界

日期：2026-09-11

## P05 评分修订

同项目任务对 `prose-polish` 0.1.2 批次做了只读复核，发现初次盲评把“读书会改至周日……无法参加请于周五18点前私信”判成了面向所有人的确认要求。这里的“无法参加”由紧邻的周日场次限定，虽然重复写出“周日”更清楚，但省略并没有把义务扩大到所有人。

冻结任务、四项标准、18 份原始输出、匿名候选顺序和盲评偏好均未修改。另存一份揭盲后的模型辅助修订评分，修正 P05 五个候选的第三项布尔值，并由原计分器重新聚合。修订前后的评分文件与结果哈希都保留在脱敏诊断证据中。

| 实验臂 | 修订前总分 | 修订后总分 | P05 完整通过 |
| --- | ---: | ---: | ---: |
| 无 Skill | 18/24 | 21/24 | 0/3 |
| 0.1.1 | 21/24 | 23/24 | 2/3 |
| 0.1.2 | 24/24 | 24/24 | 3/3 |

当前版的定向优势缩小为更稳定地保留“原定周六 → 改至周日”：当前版 3/3，旧版 2/3，基线 0/3。条件对象本身在语义校准后没有形成三组差异。该修订发生在揭盲后，评阅者仍是模型，不构成独立人工盲评。

## 隐式发现诊断

显式 `$discovery-token` 门禁此前已经通过。为测试自然任务能否触发项目 Skill，本轮增加一份两组隐式门禁：基线与项目 Skill 组收到完全相同的自然请求，隐藏令牌只存在于 `SKILL.md`。

实际单次结果中，基线没有误命中，项目 Skill 组也没有返回隐藏令牌。随后用直接指定相对路径的文件读取探针区分“没有选中 Skill”和“选中后没有读到指令”：

| 诊断 | 沙箱 | 基线 | 项目 Skill | 门禁 |
| --- | --- | --- | --- | --- |
| 自然请求 | read-only | 未命中 | 未命中 | failed |
| 直接读取 Skill 文件 | read-only | 未命中 | 未命中 | failed |
| 直接读取 Skill 文件 | workspace-write | 未命中 | 未命中 | failed |

三个运行都有完整 provider 响应，没有 MCP 或网页搜索条目。项目 Skill 组的文字提到了 `discovery-token`，并自述读取被隔离策略拦截，但原始 provider items 只有 `agent_message`，没有命令级失败轨迹。因此目前只能确认当前宿主没有完成“识别描述 → 读取正文 → 执行指令”的链路，不能确定具体由 Promptfoo、Codex SDK、Windows 隔离还是更外层权限造成。

`workspace-write` 只在一次性临时 Git 根中用于诊断，仍保持 approval never、断网、禁用网页和宿主 apps/plugins/multi-agent；它没有解决问题。常规质量对照继续默认 `read-only`。

## 影响

- 显式调用的质量结果仍有效，但不能外推到自然语言自动路由。
- 人物分析与关系类原有路由用例继续记为未覆盖，不能用这次失败当作技能本身的失败。
- 在读指令链路解决前，不继续消耗调用额度做业务 Skill 的隐式质量排名。
- `prose-polish` 继续保持 `experimental`；第六轮结论已按修订后数字收窄。

材料：

- [隐式发现宿主诊断证据](../evaluations/reports/promptfoo-implicit-discovery-host-diagnostic.json)
- [隐式发现规格](../evaluations/promptfoo/implicit-discovery.json)
- [read-only 直接文件读取规格](../evaluations/promptfoo/filesystem-read-discovery.json)
- [workspace-write 直接文件读取规格](../evaluations/promptfoo/filesystem-read-discovery-workspace-write.json)
- [修订后的第六轮报告](quality-polish-round-06.md)
- [修订后的 prose-polish 证据](../evaluations/reports/prose-preservation-0.1.2-promptfoo-diagnostic.json)
- [P05 语义等价评分校准](../evaluations/reports/prose-preservation-rubric-calibration-v1.json)
