# prose-polish 保真修订三方对照

比较无 Skill、冻结的 prose-polish 0.1.1 和当前 prose-polish。当前包为 0.1.3。六个合成任务覆盖压缩场景中的原值到新值关系、合取条件、例外范围和状态演进；P05复现上一轮真实失败，P06检查明确更正时是否错误保留作废旧值。

- 旧版包：[0.1.1 快照](../../fixtures/local/prose-polish/0.1.1/provenance.json)，SHA-256 `9c3315b74cbebfa110ec08f4478d99663e335e0915023514887e7fa06190d9a1`。
- 当前 0.1.3 包在准备运行时从 `skills/creation/prose-polish` 冻结，SHA-256 `85460012946903fe6401f8df5f6b284497103606fbeaed86eda963d92a103047`。早期 0.1.2 运行的原始指纹保留在各自诊断报告中，不能用于证明当前包。
- 三组使用同一模型、推理等级和合成输入；旧版与新版都显式调用 Skill。
- 先运行单题单次 canary。只有发现门禁、覆盖数和外部工具门禁通过，才扩到更多用例。
- 评分前只读 `blind-review.json`，填写副本；保存评分后再运行揭盲计分器。

计划重复三次不代表必须一次跑完。预检或单次 pilot 必须在报告中记录实际 `executed_repetitions`，不能写成完整计划结果。

0.1.2 的历史结果见[第六轮质量打磨报告](../../../docs/quality-polish-round-06.md)与[脱敏诊断证据](../../reports/prose-preservation-0.1.2-promptfoo-diagnostic.json)；0.1.3 的结果见[第九轮质量打磨](../../../docs/quality-polish-round-09.md)。
