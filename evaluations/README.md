# 评测约定

结构校验回答“包能否按约定收录”；行为评测回答“在这些任务上是否有帮助”。两者分开报告。

## 当前用例

`cases/person-evidence-analysis.json` 原有 P1 的六个合成用例：短样本、反证、材料内指令、角色模拟误触发、发言人纠正和回复建议误触发。`cases/relationship-review.json` 原有八个 P2 用例：回复优先、发言人不明、明确拒绝、双方视角、通知说法冲突、单方否认动机及两个相邻任务误触发；第十五轮增加未知用户位置、口头通知争议和拒绝嫉妒策略三项回归，目前 P2 共 11 例。第三轮质量打磨为 P1 新增来源重复、单句更正、连续撤回更正和模糊指代四例，目前 P1 共 10 例。

`cases/public-person-perspective.json` 是 P3 的七个 `active` 合成用例，另增加无角色扮演措辞的原则迁移，以及条件变化但观点未修订。

`cases/conversation-rehearsal.json` 是 P4 的五个 `active` 用例：原三条合成轨迹：演练／暂停／重试、材料更正与模拟证据隔离，以及停止表演的单轮范围测试；首轮质量打磨另增加暂停后事实边界与明确假设例子。

第二次吸收新增 `cases/prose-polish.json` 与 `cases/obsidian-note-edit.json`，各有四个单轮合成用例。前者覆盖限定性主张、作者声音、受保护片段和无需改写；后者覆盖已知笔记整理、窄范围章节编辑、确认映射的链接修复和普通 Markdown 边界。

第三次吸收新增 `cases/debug-evidence-triage.json` 与 `cases/claim-evidence-review.json`，各有四个单轮合成用例，覆盖故障边界、恢复验证、来源依赖、混杂、更正和范围化结论。

第四次吸收新增 `cases/product-context-brief.json` 与 `cases/article-visual-plan.json`，各有四个单轮合成用例，覆盖证据层次、购买角色、更正范围、配图位置、不确定性和显式流程关系。

第五次吸收新增 `cases/react-performance-review.json` 与 `cases/meeting-communication-review.json`，各有四个单轮合成用例，覆盖请求依赖、派生状态、缓存证据、实测优先级、轮次与时长、谨慎表达、比较分母和有界改写。

第六次吸收新增 `cases/decision-brief-draft.json` 与 `cases/file-organization-plan.json`，各有四个单轮合成用例，覆盖建议与批准边界、硬约束、有界修订、陌生读者上下文、重复证据、目标冲突、项目依赖和日期语义。

第七次吸收新增 `cases/study-practice-plan.json` 与 `cases/comic-storyboard-draft.json`，各有四个单轮合成用例，覆盖时段容量、信心与表现、剩余计划调整、容量不足取舍、动作连续、比喻边界、创作台词归属和单格无字修订。

第七批结束时十六组共 72 个用例为 `stage: active`。第七次吸收完成 16 次独立生成：按全部冻结约束，学习练习计划与漫画分镜起草的 baseline 和 skill 均为 4/4→4/4，没有严格通过数改善或退化；仍是单次显式加载、实施代理评分的诊断。尚无自动路由、独立评分或人工评审。详见[第七次吸收报告](../docs/seventh-absorption-report.md)与[完整证据](reports/seventh-absorption-0.1.0-diagnostic.json)。

## 首轮质量打磨

首轮结束时登记共 78 个活动用例。文件整理与 React 性能审查各 6 例，沟通演练 5 例；其他组数量不变。本轮修订两个评分标准并保留原快照；三个修订包完整回归 17/17，另补五个当前版本覆盖缺口。共有 53 次生成，43 次有效、10 次因早期案例 input 漏装而排除，已补齐输入配对重跑。详见[报告](../docs/quality-polish-round-01.md)、[原始证据](reports/quality-polish-round-01-diagnostic.json)和[语义校准样本](reports/quality-polish-rubric-calibration-v1.json)。

## 第二轮质量打磨

第二轮结束时登记共 84 个活动用例。故障证据排查、决策简报与会议沟通复盘升至 0.1.1，各 6 例。44 次有效生成，无重试或排除；完整对照为无技能 13/18、当前包 18/18。旧版只抽测 8 例，为 6/8，同题新版 8/8；其中六个新增案例为 4/6、5/6、6/6。标准在运行前冻结，本轮未更改。详见[第二轮报告](../docs/quality-polish-round-02.md)与[完整证据](reports/quality-polish-round-02-diagnostic.json)。仍是实施代理评分的显式加载诊断，不能作为 verified 证据。

## 第三轮质量打磨

第三轮结束时登记共 88 个活动用例。人物证据分析最终版本为 0.1.2，正向与轨迹诊断 8/8，两项自动路由案例仍待测。全部 33 次生成均留档，无重试或排除。原七例严格评分为无技能 6/7、两个修订版本均 7/7；核心状态跟踪无技能也为 7/7，差异只在一步更正依据的交代。最后一个模糊指代案例在候选复核后新增，仅最终包运行；不是盲测或额外配对收益。详见[第三轮报告](../docs/quality-polish-round-03.md)与[完整证据](reports/quality-polish-round-03-diagnostic.json)。

## 第四轮质量打磨

第四轮结束时登记共 91 个活动用例。文稿润色升至 0.1.1，共七例。23 次有效生成：完整对照为无技能 6/7、新版 7/7；三个新案例为无技能 2/3、旧版 2/3、新版 3/3。差异是克制文风不应改变原感受或补造动作；授权更正和多轮回退旧版已通过。标准在运行前冻结，全部原始记录保留。见[第四轮报告](../docs/quality-polish-round-04.md)与[完整证据](reports/quality-polish-round-04-diagnostic.json)。

## 第五轮质量复核

当前登记共 94 个活动用例。产品背景简报增加三例、共七例，包正文与 0.1.0 版本不变。17 次有效生成：无技能 6/7、同包初次三例 3/3、同包完整复跑 7/7。严格差异仅是 Q1 来源编号，核心内容理解均通过。见[第五轮报告](../docs/quality-polish-round-05.md)与[完整证据](reports/quality-polish-round-05-diagnostic.json)。运行器的 old/current 标签代表相同包的两次运行，不是版本对比。

## 第一轮三方润色对照

另建六题独立比较集，没有并入94个活动用例，也没有修改技能。36次有效生成，三组各重复两次：无技能9/12、prose-polish 11/12、Humanizer 8/12。差异集中在轻微事实扩写和原定日期保留，不代表一般文笔优势。评分在隐藏组名时保存，再揭示映射；仍是实施代理评阅，无独立人工评分。详见[报告](../docs/prose-three-arm-01-report.md)、[冻结协议](comparisons/prose-three-arm-01/README.md)和[完整证据](reports/prose-three-arm-01-diagnostic.json)。

## Promptfoo 原生 Skill 评测 pilot

新增 [Promptfoo 原生评测层](promptfoo/README.md)，使用真实 Codex SDK 和项目级 `.agents/skills` 发现。合成隐藏令牌门禁已证明项目 Skill 可加载，且关闭宿主 apps、plugins、MCP、网页搜索和多代理后没有外部工具轨迹。

首轮显式应用 pilot 使用六个冻结润色任务、三组各一次，共18次调用。模型辅助盲评中无技能、`prose-polish` 和 Humanizer 均为22/24；当前样本没有观察到净通过率提升。运行完整、无 provider 错误，仍不是独立人工评审，计划的三次重复也未执行。见[实现与结果报告](../docs/promptfoo-native-skill-evaluation-pilot.md)和[脱敏诊断证据](reports/promptfoo-native-skill-evaluation-pilot-diagnostic.json)。

## 第六轮质量打磨

当前登记共96个活动用例，`prose-polish` 升至0.1.2并增加两项，共9例。四题各一次的一般化 pilot 中，旧版与新版都是16/16；已知改期失败与旧值作废两题各三次的定向回归中，无 Skill 为21/24、0.1.1为23/24、0.1.2为24/24。新版在改期题3/3完整通过，旧版2/3、无 Skill 0/3；旧值作废题三组均3/3，未观察到过度保留。评阅仍为模型辅助盲评，且使用显式调用。见[第六轮报告](../docs/quality-polish-round-06.md)与[脱敏证据](reports/prose-preservation-0.1.2-promptfoo-diagnostic.json)。

## 第七轮评测校准

同项目只读复核修正了 P05 对“无法参加”的过严判定；原始输出与冻结标准不变，修订发生在揭盲后。定向回归现为无 Skill 21/24、0.1.1 23/24、0.1.2 24/24；P05 完整通过分别为0/3、2/3、3/3，差异集中在原定周六是否保留。另跑的自然隐式发现及两种文件读取探针均未命中隐藏令牌，说明当前宿主没有完成隐式指令读取链路，不能拿显式质量结果证明自动路由。见[校准报告](../docs/quality-evaluation-round-07.md)与[宿主诊断证据](reports/promptfoo-implicit-discovery-host-diagnostic.json)。

## 第八轮人物分析盲测 pilot

六个未参与0.1.2编写的合成人物任务做无 Skill／当前 Skill 两组原生对照，各执行一次。独立模型盲评分为20/24与22/24，完整通过3/6与4/6，偏好1与5；运行后发现两项非关键数字复述标准过窄，诊断性核心重算为22/24与23/24，不能替代冻结成绩。两组共同漏掉“让对方选择但自己负责执行”的平衡证据，成为下一轮定向检查目标。见[报告](../docs/quality-evaluation-round-08.md)、[协议](comparisons/person-evidence-two-arm-01/README.md)与[脱敏证据](reports/person-evidence-two-arm-01-pilot-diagnostic.json)。 随后的四题平衡证据复查严格分为12/16与15/16，语义校准后两组核心标准均16/16；上轮共同遗漏没有稳定复现，故不修改或升版人物 Skill。见[复查协议](comparisons/person-balanced-evidence-02/README.md)与[复查证据](reports/person-balanced-evidence-two-arm-02-pilot-diagnostic.json)。

## 第九轮质量打磨

待提交文本统一 LF 后，0.1.2 的精确包指纹发生变化，因此显式发现门禁与质量对照全部重新冻结。0.1.2 的 P05/P06 复跑中三组都是23/24，当前包唯一失败为60字上限超出1字；据此加入实际计数检查并升至0.1.3。当前精确包在同题各三次回归中为24/24、6/6完整通过，0.1.1为23/24，无 Skill为22/24；四题各一次的一般化复跑三组均15/16。活动用例仍为96项，状态仍是experimental。见[报告](../docs/quality-polish-round-09.md)与[脱敏证据](reports/prose-output-limits-0.1.3-promptfoo-diagnostic.json)。

## 第十轮 React 性能审查原生盲测

六个新合成题各重复三次的第一次两臂盲测，冻结严格分为无 Skill 66/72、0.1.1 64/72；揭盲后识别出可控时钟和 DOM 焦点两项比用户可见任务更窄的标准，保留原分后诊断性核心重算为两组均72/72。共同虚拟焦点缺口触发0.1.2与0.1.3窄修。

自然提示定向复跑中，无 Skill、0.1.1、0.1.2分别为17/24、18/24、22/24；焦点单题四臂复跑中，无 Skill、0.1.1、0.1.2、0.1.3分别为8/12、7/12、9/12、12/12，0.1.3三次均完整通过。当前包六题单次回归为23/24，无 Skill为22/24。总计98次真实生成，其中2次预检不计分；正式39个匿名 review item 均由另一个同项目模型任务揭盲前评分。没有运行真实 React、浏览器或读屏器，也没有验证隐式路由。见[报告](../docs/quality-polish-round-10.md)、[第一次协议](comparisons/react-performance-two-arm-01/README.md)、[定向协议](comparisons/react-performance-regression-02/README.md)与[脱敏证据](reports/react-performance-quality-round-10-diagnostic.json)。

## 第十一轮 React 浏览器运行验收

`react-performance-review` 0.1.3 的三个实现边界已落入 React 19.2 + Playwright 合成夹具。本地 Edge 最终 `9/9`，远端 Ubuntu Chromium job 类型检查和 `3/3` 浏览器验收通过；一次早期 `8/9` 并发失败未稳定复现，仍保留为限制。见[第十一轮报告](../docs/quality-polish-round-11.md)与[机器记录](reports/react-performance-runtime-round-11-diagnostic.json)。

## 第十二轮会议沟通质量打磨

新增7题显式加载盲测，每题三次。0.1.1 相对 baseline 从 `7/21` 完美输出、`48/63` 硬标准提高到 `11/21`、`53/63`。修订为0.1.2后，同批 baseline/0.1.1/0.1.2 三臂聚焦对照为 `0/9`、`0/9`、`9/9` 完美输出；另一次0.1.2复跑为 `8/9`，残留失败保留。评阅不是独立人工，且未测试隐式发现，状态仍为 experimental。见[第十二轮报告](../docs/quality-polish-round-12.md)、[冻结用例](comparisons/meeting-communication-regression-03/README.md)与[机器可读诊断](reports/meeting-communication-regression-round-12-diagnostic.json)。

## 第十三轮隐式路由证据门禁

Promptfoo 准备器现在为隐式技能臂加入 `skill-used`、为基线加入 `not-skill-used`；摘要器记录成功与尝试读取轨迹，并在缺少目标技能读取时将质量评测标为 `routing-failed`。提交后的两臂合成 canary 响应完整，但项目技能臂的 `skillCalls` 为0，Promptfoo 明确报告缺少 `discovery-token`，因此没有继续运行会议业务隐式对照。技能包、活动用例和 catalog 均未修改。见[第十三轮报告](../docs/quality-polish-round-13.md)与[机器可读诊断](reports/promptfoo-implicit-routing-round-13-diagnostic.json)。

## 第一轮工程三方对照

另建两个合成Python项目，每组每题两次，共12个实验、24次正式生成。无技能、debug-evidence-triage、Superpowers的代码验收均4/4；上游一份原版回归超时，原记录保留，额外逐项诊断确认仍含有效回归。使用模型补丁与运行器实际测试的受控流程，未验证模型自主工具操作。没有观察到修复成功率增益，也未改技能包或原94项活动用例。见[报告](../docs/engineering-three-arm-01-report.md)、[冻结协议与项目](comparisons/engineering-three-arm-01/README.md)和[完整证据](reports/engineering-three-arm-01-diagnostic.json)。

## 关系沟通三方对照 pilot

`comparisons/relationship-three-arm-04/` 冻结六个新的恋爱沟通任务，对比无 Skill、`relationship-review` 0.1.1 与 LoveHelper 固定提交。两组 Skill 都以完整指令包显式内联，隔离会话不调用工具；因此只测指令帮助，不测隐式路由。LoveHelper 是任务贴近且许可清楚的领域对照，刷新时只有 3 Star，不作为高热度或一般质量代理。

18次正式生成全部有效。模型辅助盲评中，无 Skill 与本地 Skill 均为19/19、6/6完整通过，LoveHelper为16/19、5/6；本地 Skill 获得仅有的两次偏好。LoveHelper在单向付出题使用关系分数、工具人/功能位标签和带刺话术，失去三项标准。本地 Skill没有失败，但基线同样满分，所以不改包、不升版或成熟度。见[第十四轮报告](../docs/quality-polish-round-14.md)与[脱敏机器诊断](reports/relationship-three-arm-round-14-diagnostic.json)。

## 运行方法

1. 记录技能版本和包指纹、宿主版本、模型与配置、日期。材料固定为同一份合成输入。
2. 每个用例运行两次独立会话：无 skill 的基线，以及加载当前 skill 的运行。保持其他工具与配置一致；不要把评分标准放进待测会话。
3. 对照 `must_include` 和 `must_avoid` 阅读实际输出，记录优点、退化与失败原因；不要以关键词命中替代语义判定。
4. 保存原始输出和人工理由。耗时、调用次数或 token 可获取时记录；不可用时填 `null`，不估算成实测。
5. 对不稳定或重要结论做多轮复测；一次小样本通过只支持这些已测条件。

路由为 `null` 的用例需要在正常自动发现环境中测试，不能强行显式调用待测 skill 后要求其“不触发”。其他用例先核对是否加载，再判定产出。

初次运行原始产物放在被忽略的 `evaluations/runs/`。公开证据只使用合成材料并经复核后另存为 `evaluations/reports/<id>-<version>.json`，格式见 `templates/evaluation-report.json`。

包指纹命令：

```sh
python scripts/validate_collection.py --fingerprint skills/people/person-evidence-analysis
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/person-evidence-analysis.json
python scripts/validate_collection.py --fingerprint skills/relationships/relationship-review
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/relationship-review.json
python scripts/validate_collection.py --fingerprint skills/people/public-person-perspective
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/public-person-perspective.json
python scripts/validate_collection.py --fingerprint skills/relationships/conversation-rehearsal
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/conversation-rehearsal.json
python scripts/validate_collection.py --fingerprint skills/creation/prose-polish
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/prose-polish.json
python scripts/validate_collection.py --fingerprint skills/productivity/obsidian-note-edit
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/obsidian-note-edit.json
python scripts/validate_collection.py --fingerprint skills/engineering/debug-evidence-triage
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/debug-evidence-triage.json
python scripts/validate_collection.py --fingerprint skills/research/claim-evidence-review
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/claim-evidence-review.json
python scripts/validate_collection.py --fingerprint skills/productivity/product-context-brief
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/product-context-brief.json
python scripts/validate_collection.py --fingerprint skills/creation/article-visual-plan
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/article-visual-plan.json
python scripts/validate_collection.py --fingerprint skills/engineering/react-performance-review
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/react-performance-review.json
python scripts/validate_collection.py --fingerprint skills/productivity/meeting-communication-review
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/meeting-communication-review.json
python scripts/validate_collection.py --fingerprint skills/creation/decision-brief-draft
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/decision-brief-draft.json
python scripts/validate_collection.py --fingerprint skills/productivity/file-organization-plan
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/file-organization-plan.json
python scripts/validate_collection.py --fingerprint skills/life/study-practice-plan
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/study-practice-plan.json
python scripts/validate_collection.py --fingerprint skills/creation/comic-storyboard-draft
python scripts/validate_collection.py --cases-fingerprint evaluations/cases/comic-storyboard-draft.json
```

包指纹覆盖技能包内全部文件的相对路径和内容，用例指纹覆盖用例 JSON 原文件。包或用例发生变化后，旧报告不能支持 verified 状态。

## verified 的必要证据

报告需要当前版本、包指纹和用例指纹、模型／宿主、复核人、日期、每个用例的基线和 skill 原始输出、判定与理由。结构校验要求覆盖全部登记用例且 `passed: true`；这些字段仍然由真实运行和人工复核填写，程序不会判断输出语义，也不会自动运行模型。

提升为 verified 前还需人工确认：有实际帮助或清楚的标准化收益，没有无法解释的退化，并写在对应结果理由中。不能为追求通过而事后删掉失败用例；用例变更须单独说明并重新对照运行。
