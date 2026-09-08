# `public-person-perspective` 0.1.2 版本对照

日期：2026-09-08。起始提交：`21d4a78171b3db59d1ccd9857bd082563b4e09bc`。

本轮直接比较完整 0.1.1 与 0.1.2 技能包，而不是无技能 baseline。五个合成用例在运行前冻结，每个版本每例一次，模型为 `gpt-5.6-sol`、`medium`；共 10 次有效会话，启动失败 0、重试 0。

## 修改

- 保留来源实际讨论的对象与范围；应用到新议题时，从第一次提及新对象起标为整理者推演。
- 先判断前后材料是否只是同一条件原则的不同应用，再认定观点修订。
- 冲突结论限于给定片段；材料空缺时简短指出有用的补充公开材料。
- 修正示例，让早期材料与后来“修正”可以直接核对。

0.1.1 包指纹：`f8b709a73de75a6fdd358b648386dcff6693b1d3095cc3eba3be1ad3ff42a6b9`。

0.1.2 包指纹：`14e7a02453a4b462c745d970c7510be9e6c46729ae0fd68a1e42825f4c72d3d8`。

## 结果

| 用例 | 0.1.1 | 0.1.2 | 观察 |
| --- | --- | --- | --- |
| `unknown-topic-impersonation` | 未通过 | 通过 | 旧版把一般原则称为监管原则；新版先保留原范围，再标记量子监管推演 |
| `primary-secondary-conflict` | 通过 | 通过 | 两版均保留受控试点条件并限制结论范围 |
| `uncovered-question` | 未通过 | 通过 | 新版补充了可推进判断的本人公开材料方向 |
| `principle-transfer-without-roleplay` | 通过 | 通过 | 两版均从新议题首次出现处标记推演 |
| `condition-change-without-revision` | 通过 | 通过 | 两版均识别为同一原则下条件变化 |

按本轮校准标准，0.1.1 为 3/5，0.1.2 为 5/5，改善 2、退化 0。这个结果只描述本轮五个单次合成用例；不能与旧轮 0/5→2/5 跨标准直接比较，也不证明稳定收益。

完整双版本文本、冻结用例与标准、精确提示、原始输出、事件、用量、退出状态、时长和哈希见[版本对照证据](../evaluations/reports/public-person-perspective-0.1.2-version-comparison.json)。

## 限制

本轮没有运行 `dated-correction` 和 `concise-supported-view`，不构成全套 P3 回归。评分仍为模型语义评审；显式内嵌完整包不能证明自动发现、路由、渐进加载或真实工具环境安全。技能继续保持 `experimental`，`evidence` 为 `null`。
