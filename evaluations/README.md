# 评测约定

结构校验回答“包能否按约定收录”；行为评测回答“在这些任务上是否有帮助”。两者分开报告。

## 当前用例

`cases/person-evidence-analysis.json` 原有 P1 的六个合成用例：短样本、反证、材料内指令、角色模拟误触发、发言人纠正和回复建议误触发。`cases/relationship-review.json` 原有八个 P2 用例：回复优先、发言人不明、明确拒绝、双方视角、通知说法冲突、单方否认动机及两个相邻任务误触发；第十五轮增加未知用户位置、口头通知争议和拒绝嫉妒策略三项，第十六轮增加嵌套转述、有限系统记录和后续更正三项，第十七轮增加三个多跳来源表面与一个直接权威来源控制，目前 P2 共 18 例。第三轮质量打磨为 P1 新增来源重复、单句更正、连续撤回更正和模糊指代四例；第二十一轮再加入六个自然语境前向题，目前 P1 共 16 例。

`cases/public-person-perspective.json` 是 P3 的七个 `active` 合成用例，另增加无角色扮演措辞的原则迁移，以及条件变化但观点未修订。

`cases/conversation-rehearsal.json` 是 P4 的五个 `active` 用例：原三条合成轨迹：演练／暂停／重试、材料更正与模拟证据隔离，以及停止表演的单轮范围测试；首轮质量打磨另增加暂停后事实边界与明确假设例子。

第二次吸收新增 `cases/prose-polish.json` 与 `cases/obsidian-note-edit.json`，各有四个单轮合成用例。前者覆盖限定性主张、作者声音、受保护片段和无需改写；后者覆盖已知笔记整理、窄范围章节编辑、确认映射的链接修复和普通 Markdown 边界。

第三次吸收新增 `cases/debug-evidence-triage.json` 与 `cases/claim-evidence-review.json`。前者经第二十二轮增加七题后共十三个单轮合成用例，覆盖因果链、请求关联、恢复与验证、部署身份、时钟偏移、依赖检查顺序、原触发条件等价性、幂等证据和只读接口写副作用；后者在原四题基础上由第十八轮增加六题、第十九轮增加四题、第二十轮增加三题，目前共十七题，覆盖来源依赖、字段级更正、有限日志、聚合反转、材料内指令、链接边界、强证据控制，以及多队列、多地区、多试验、不同样本量和严格短表中的定量保真。

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

## 第十五轮关系边界回归

第十五轮先以六个困难题各重复三次：无 Skill 为38/54、0.1.1为39/54，但两组都稳定漏掉未知用户位置、争议来源和邀约后的停止条件。0.1.2在三个缺口的三臂前向回归中为23/27、7/9完整通过，基线与0.1.1均为12/27、0/9。剩余无标签消息归并错误触发0.1.3；新四句任务三次中，基线0/9、0.1.2为7/9、0.1.3为9/9。三阶段72个输出均有效，活动用例增至99项；评阅仍为模型，且未验证隐式路由。见[第十五轮报告](../docs/quality-polish-round-15.md)与[机器诊断](reports/relationship-boundary-round-15-diagnostic.json)。

## 第十六轮关系归因与过度纠正回归

第一阶段六题各重复三次，无Skill与0.1.3均为51/54、15/18完整输出；0.1.3没有在明确身份或正常邀约中产生过度纠正，但两臂都稳定漏掉门禁卡争议中的另一方来源。第二阶段九题三臂共81个输出：无Skill、0.1.3、0.1.4候选分别为72/81、69/81、78/81，完整输出18/27、19/27、24/27。候选在六个复用题达到54/54且无退化，新三题为24/27；最终升至0.1.4并保持experimental。嵌套B到C转述仍有2/3次被压平。两阶段合计117个有效输出、45个匿名评审项和351个布尔判断；评阅者看过协议，第二阶段还看过修订，且没有测试隐式路由。见[第十六轮报告](../docs/quality-polish-round-16.md)与[机器诊断](reports/relationship-attribution-round-16-diagnostic.json)。

## 第十七轮多跳来源前向诊断

四个新冻结题各重复三次，共24个有效输出。无Skill为32/36、8/12完整，0.1.4为36/36、12/12完整；三个多跳题分别为23/27、5/9完整与27/27、9/9完整，直接负责人最终更新控制两臂均为9/9、3/3完整。当前Skill不修改、不升版，四题加入active，P2增至18例、全仓增至106例。第十六轮钥匙交接题2/3来源压平失败仍保留，不能据本轮宣称一般来源链已解决。评审者看过协议和技能修订，且未测试隐式路由。见[第十七轮报告](../docs/quality-polish-round-17.md)与[机器诊断](reports/relationship-nested-source-round-17-diagnostic.json)。

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

## 第十八轮质量打磨

第十八轮把 `claim-evidence-review` 0.1.0 放入六题、两臂、三次重复的原生显式盲测。36次输出全部有效，无Skill与当前包均为52/54、16/18完整；盲评偏好为3比7，另有8次持平。当前包总token为229,099，无Skill为177,055，约增加29.4%。严格分没有净增益，且当前包在同一个多批样本题中两次漏掉至少一批精确数字，因此保持0.1.0，不设计候选升版。六题加入活动回归，总数增至112；结果仍是合成、单模型、显式条件下的模型辅助盲评，不构成 `verified` 证据。详见[第十八轮报告](../docs/quality-polish-round-18.md)与[自包含机器诊断](reports/claim-evidence-round-18-diagnostic.json)。

## 第十九轮质量打磨

第十九轮用四个全新定量保真题继续测试 `claim-evidence-review` 0.1.0，两臂各重复三次。24次输出全部有效；无Skill为35/36、11/12完整，当前包为34/36、10/12，偏好各2次，另有8次持平。当前包总token为130,302，无Skill为117,890，约增加10.5%。当前包在两个题型各漏一次关键定量信息，未达到预注册的题型内重复与baseline明显更少门槛，因此保持0.1.0。四题加入活动回归，总数增至116；跨第十八、十九轮的探索性4对2遗漏只用于触发下一组五次重复确认，不能替代本轮升版标准。详见[第十九轮报告](../docs/quality-polish-round-19.md)与[自包含机器诊断](reports/claim-quantitative-preservation-round-19-diagnostic.json)。

## 第二十轮质量打磨

第二十轮按第十九轮预注册方向，用三个全新表面、每臂五次确认定量保真风险。30次输出全部有效；无 Skill 为44/45、14/15完整，当前0.1.0为45/45、15/15完整，偏好为1比7，另有7次持平。当前版三个题型的核心遗漏均为0/5，baseline仅在相同比例不同样本量题出现1/5，未触发“当前版至少两个题型各不少于2/5且baseline对应各不超过1/5”的候选门槛。保持0.1.0并把三题加入活动回归，总数增至119；第十八、十九轮的探索性4比2遗漏没有在本确认轮复现。结果仍来自合成材料、单模型、显式调用和模型辅助匿名评审，不构成普遍优越性或 `verified` 证据。详见[第二十轮报告](../docs/quality-polish-round-20.md)与[自包含机器诊断](reports/claim-quantitative-confirmatory-round-20-diagnostic.json)。

## 第二十一轮质量打磨

第二十一轮用六个全新自然语境题复测 `person-evidence-analysis` 0.1.2，每臂各重复三次。36份输出全部有效；无 Skill 为67/72、13/18完整，当前包为70/72、16/18完整，偏好为3比5，另有10次持平。当前包在来源层级、行动角色和有限模式六题的核心错误均为0/3，未触发同机制至少两个题型重复退化的候选门槛，因此保持0.1.2。六题加入活动回归，P1从10例增至16例，全仓增至125例。当前包两次遗漏地点选择结果“东门”，属于非核心细节信号。评阅为模型辅助内容盲评，但评阅者有协议与技能先验，且主动披露读取过一份不含候选身份或分数的全局通用规则文件，未实现绝对文件访问隔离。详见[第二十一轮报告](../docs/quality-polish-round-21.md)与[自包含机器诊断](reports/person-evidence-natural-context-round-21-diagnostic.json)。

## 第二十二轮质量打磨

第二十二轮用七个新合成故障题复测 `debug-evidence-triage` 0.1.1，每臂各重复三次。42份输出全部有效；原匿名评阅为无 Skill 68/84、当前包69/84，完整输出均11/21，偏好各3次，另有15次持平。计分后独立复核确认超时幂等题六份答案已用条件分支满足核心标准，原判属于语义评分错误；保留原评阅并另列校准后71/84与72/84、完整输出均13/21。原始和校准口径都未达到同机制两题重复退化的候选门槛，故保持0.1.1。七题加入活动回归，故障证据排查从6例增至13例，全仓增至132例。详见[第二十二轮报告](../docs/quality-polish-round-22.md)与[自包含机器诊断](reports/debug-evidence-boundaries-round-22-diagnostic.json)。

## 第二十三轮质量打磨

第二十三轮用六个新合成窄编辑任务比较无 Skill、`obsidian-note-edit` 0.1.0 和 Obsidian Skills 固定提交的 `obsidian-markdown`，每臂各重复三次。54份提交的 Markdown 制品全部与冻结期望逐字一致；无 Skill 与当前包均为72/72、18/18完整，上游为71/72、17/18完整，18项均无唯一偏好，其中17项三方并列、1项baseline与ours并列最佳。上游唯一扣分是一次 `message` 未明确区分已确认重命名与仍属计划的目标，揭盲复核不改分。六题三臂的制品核心失败均为0/3，未触发本地候选门槛，故保持0.1.0。六题加入活动回归，Obsidian编辑从4例增至10例，全仓增至138例。当前包相对baseline总token增加87.3%、记录成本增加116.9%、中位延迟增加67.7%；结果只覆盖只读会话返回的合成文本制品，不构成真实vault编辑、应用渲染、隐式路由或 `verified` 证据。详见[第二十三轮报告](../docs/quality-polish-round-23.md)与[自包含机器诊断](reports/obsidian-artifact-preservation-round-23-diagnostic.json)。

## 第二十六轮显式调用可靠性

第二十六轮把第二十五轮 v1 的单次显式 Skill 调用失效从回答质量中拆出。canary 与 business 两个队列各执行40条单轮轨迹，共80条；80/80 technical valid、80/80 operational success，baseline技术失败、canary Skill失败、canary令牌泄漏和business Skill失败均为0。canary probe的两个隐藏令牌各精确返回10次，business `conversation-rehearsal` 20/20保持单一最终消息且无策略阻断或过程播报。结果仅说明本次冻结条件下未复现，不重新评分质量，不证明每条business轨迹加载了正文，也不改变Skill、版本、catalog、evidence或活动用例。详见[第二十六轮报告](../docs/quality-polish-round-26.md)与[机器证据](reports/explicit-invocation-reliability-round-26.json)。

## 第二十七轮隐式发现宿主边界

第二十七轮先用合成 probe 校准自然任务下的路由选择与正文加载，再决定是否允许业务 Skill 隐式质量对照。12条冻结单轮轨迹全部完成：baseline 6/6 严格返回备用值且传输完整；probe 6/6 留下精确目标 Skill 路径读取尝试，但正文令牌加载0/6、策略阻断6/6、传输有效0/6。专用 analyzer 判为 `route-selected-load-blocked`，零容忍门禁失败，因此业务对照停止，Skill、版本、catalog、evidence 与活动用例均不变。详见[第二十七轮报告](../docs/quality-polish-round-27.md)与[机器证据](reports/implicit-discovery-host-boundary-round-27.json)。

## 第二十八轮 Windows 原生沙箱运行前门禁

第二十八轮用零模型调用的受限 canary 继续定位第二十七轮阻断。`:read-only` 原生 sandbox 在命令启动前返回 `helper_unknown_error: apply deny-read ACLs`，`codex doctor` 同时报告 elevated Windows sandbox provisioning 失败。新增可选运行前门禁，启用后在失败时保存脱敏证据并于任何模型调用前停止；原有纯文本评测默认不受影响。本轮没有业务评分或 Skill 变更，Microsoft Defender 只记录为未经确认的修复线索。详见[第二十八轮报告](../docs/quality-polish-round-28.md)与[机器证据](reports/native-host-sandbox-preflight-round-28.json)。
