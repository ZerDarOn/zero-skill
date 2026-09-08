# 评测约定

结构校验回答“包能否按约定收录”；行为评测回答“在这些任务上是否有帮助”。两者分开报告。

## 当前用例

`cases/person-evidence-analysis.json` 是 P1 的六个合成用例：短样本、反证、材料内指令、角色模拟误触发、发言人纠正和回复建议误触发。`cases/relationship-review.json` 有六个 P2 用例：回复优先、发言人不明、明确拒绝、双方视角及两个相邻任务误触发。两组共 12 个用例。

两组用例现为 `stage: active`，表示对应技能已经实现并登记；有用例仍不代表已进行或通过行为评测。首批范围和实际结果见[执行说明](../docs/first-absorption-handoff.md)与[吸收报告](../docs/first-absorption-report.md)。

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
```

包指纹覆盖技能包内全部文件的相对路径和内容，用例指纹覆盖用例 JSON 原文件。包或用例发生变化后，旧报告不能支持 verified 状态。

## verified 的必要证据

报告需要当前版本、包指纹和用例指纹、模型／宿主、复核人、日期、每个用例的基线和 skill 原始输出、判定与理由。结构校验要求覆盖全部登记用例且 `passed: true`；这些字段仍然由真实运行和人工复核填写，程序不会判断输出语义，也不会自动运行模型。

提升为 verified 前还需人工确认：有实际帮助或清楚的标准化收益，没有无法解释的退化，并写在对应结果理由中。不能为追求通过而事后删掉失败用例；用例变更须单独说明并重新对照运行。
