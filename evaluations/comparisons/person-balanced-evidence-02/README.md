# 人物分析平衡证据定向检查 02

这组比较不修改 Skill，先检查上一轮 E05 的“选择权交给别人时遗漏自己承担执行”是否能在不同场景重复出现。四个合成任务覆盖优先级选择、报价风险委托、当下拒绝与后续承诺，以及只问决策归属的简短反例。

无 Skill 与当前 `person-evidence-analysis` 使用相同模型和输入，本地 Skill 显式调用。计划三次重复，先做一次 pilot；只有出现稳定且可泛化的失败，才冻结旧包并考虑修改。

实际 pilot 与校准结果见[第八轮质量检查](../../../docs/quality-evaluation-round-08.md)及[脱敏诊断证据](../../reports/person-balanced-evidence-two-arm-02-pilot-diagnostic.json)。
