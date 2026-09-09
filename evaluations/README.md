# 评测约定

结构校验回答“包能否按约定收录”；行为评测回答“在这些任务上是否有帮助”。两者分开报告。

## 当前用例

`cases/person-evidence-analysis.json` 是 P1 的六个合成用例：短样本、反证、材料内指令、角色模拟误触发、发言人纠正和回复建议误触发。`cases/relationship-review.json` 有八个 P2 用例：回复优先、发言人不明、明确拒绝、双方视角、通知说法冲突、单方否认动机及两个相邻任务误触发。两组共 14 个用例。

`cases/public-person-perspective.json` 是 P3 的七个 `active` 合成用例，另增加无角色扮演措辞的原则迁移，以及条件变化但观点未修订。

`cases/conversation-rehearsal.json` 是 P4 的三个 `active` 合成轨迹：演练／暂停／重试、材料更正与模拟证据隔离，以及停止表演的单轮范围测试。

第二次吸收新增 `cases/prose-polish.json` 与 `cases/obsidian-note-edit.json`，各有四个单轮合成用例。前者覆盖限定性主张、作者声音、受保护片段和无需改写；后者覆盖已知笔记整理、窄范围章节编辑、确认映射的链接修复和普通 Markdown 边界。

第三次吸收新增 `cases/debug-evidence-triage.json` 与 `cases/claim-evidence-review.json`，各有四个单轮合成用例，覆盖故障边界、恢复验证、来源依赖、混杂、更正和范围化结论。

第四次吸收新增 `cases/product-context-brief.json` 与 `cases/article-visual-plan.json`，各有四个单轮合成用例，覆盖证据层次、购买角色、更正范围、配图位置、不确定性和显式流程关系。

十组共 48 个用例现为 `stage: active`。第四次吸收完成 16 次独立生成：按全部冻结约束，产品背景简报 baseline 与 skill 为 2/4→4/4，文章配图规划为 4/4→4/4；仍是单次显式加载、执行模型评分的诊断。尚无自动路由、独立评分或人工评审。详见[第四次吸收报告](../docs/fourth-absorption-report.md)与[完整证据](reports/fourth-absorption-0.1.0-diagnostic.json)。

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
```

包指纹覆盖技能包内全部文件的相对路径和内容，用例指纹覆盖用例 JSON 原文件。包或用例发生变化后，旧报告不能支持 verified 状态。

## verified 的必要证据

报告需要当前版本、包指纹和用例指纹、模型／宿主、复核人、日期、每个用例的基线和 skill 原始输出、判定与理由。结构校验要求覆盖全部登记用例且 `passed: true`；这些字段仍然由真实运行和人工复核填写，程序不会判断输出语义，也不会自动运行模型。

提升为 verified 前还需人工确认：有实际帮助或清楚的标准化收益，没有无法解释的退化，并写在对应结果理由中。不能为追求通过而事后删掉失败用例；用例变更须单独说明并重新对照运行。
