# 评测约定

结构校验回答“包能否按约定收录”；行为评测回答“在这些任务上是否有帮助”。两者分开报告。

## 当前用例

`cases/person-evidence-analysis.json` 原有 P1 的六个合成用例：短样本、反证、材料内指令、角色模拟误触发、发言人纠正和回复建议误触发。`cases/relationship-review.json` 有八个 P2 用例：回复优先、发言人不明、明确拒绝、双方视角、通知说法冲突、单方否认动机及两个相邻任务误触发。第三轮质量打磨为 P1 新增来源重复、单句更正、连续撤回更正和模糊指代四例，目前 P1 共 10 例、P2 共 8 例。

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
