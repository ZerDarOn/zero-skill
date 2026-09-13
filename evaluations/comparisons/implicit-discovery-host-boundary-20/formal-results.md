# Round 27 正式结果

日期：2026-09-13

## 结论

冻结的 12 条单轮轨迹全部完成，隐式发现门禁未通过。baseline 6/6 严格返回备用值且传输完整；probe 6/6 都留下精确目标 Skill 路径的读取尝试，因此路由选择为 6/6，但正文令牌加载为 0/6，策略阻断为 6/6，传输有效为 0/6。

专用 analyzer 将结果归类为 `route-selected-load-blocked`。这说明两个自然触发表面都使模型选择了目标路由，随后宿主阻止正文读取；它不说明业务 Skill 的自动触发质量，也不构成业务 Skill 退化。

| 臂 | 尝试 | route selected | body loaded | policy blocked | transport valid | operational success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 6 | 0 | 0 | 0 | 6 | 6 |
| probe | 6 | 6 | 0 | 6 | 0 | 0 |

probe 的六条轨迹都返回了备用值。每条还先输出一条 Skill 加载过程消息，再输出最终备用值，因此同时触发 `agent-message-count-failure` 与 `output-binding-failure`；这些失败均原样保留，没有补跑、筛选或替换。

## 门禁决定

baseline 的路由误判、令牌泄漏、备用输出缺失、策略阻断和传输失败均为 0。probe 的路由缺失为 0，但正文加载失败、策略阻断和传输失败均为 6，超过冻结上限 0。

因此：

- `business_comparison_authorized=false`；
- `infrastructure_investigation_opened=true`；
- `skill_change_authorized=false`。

本轮按协议停止，没有运行任何业务 Skill 的隐式回答质量对照，也没有修改 Skill、版本、catalog、evidence 或活动用例。

## 运行边界

协议与分析器在提交 `6cb20962d7ee679da829278434d07a35d3a5a101` 冻结并推送后，才创建正式目录 `implicit-discovery-host-boundary-20-formal-20260913-v1`。运行使用 `gpt-5.6-sol`、medium、项目级隐式安装、只读沙箱、隔离 HOME/CODEX_HOME，并关闭网络、apps、plugins 和 multi-agent。

两题、两臂各重复三次，共 12 条；按种子 `270913` 确定性乱序后交给 4 个 worker。baseline 与 probe 的题面逐字相同，题面不含 Skill id、路径或正文令牌。预检与正式目录分开，正式结果没有混入探索样本。

## 原始证据指纹

正式原始目录由 `.gitignore` 排除，公开机器报告保存每条轨迹的分类投影和以下 SHA-256。本机保留 raw artifacts 时，测试会重新运行分类并比对公开证据。

| 制品 | SHA-256 |
| --- | --- |
| `frozen.json` | `d72c2deafcf3279befc5843b763bb56b7996a62bae119de127295f2ca89b544b` |
| `run-meta.json` | `d345b48b9bf72bd77ba49dc09d8fff8157869ab6759e3622317abcc80a8e9852` |
| `native-results.json` | `4e6679834b8785d572ebf901fa4258548dfe65d4f8777f9f33ad546135e56884` |
| `implicit-discovery-analysis.json` | `1345dc99585202160381c0e1d132db08b83837f30469e09dde8f151e0f687e29` |
| job order | `044491b1b4aaa1062f7c3953c7a12ce9db27f688ad4e7dae06abcc00cd05a86f` |

## 限制

样本只覆盖当前主机、一个模型与推理等级、两个合成自然触发表面和项目级 Skill 安装。路由选择来自精确读取尝试，不等于正文加载成功；0/6 正文加载是当前宿主执行边界的观测，不应推广到其他 Codex 版本、沙箱策略、安装位置或模型。

本轮是基础设施诊断，不评分答案质量。后续应先修复或澄清宿主对项目 Skill 正文读取的策略，再用新的冻结 canary 复测；在 canary 门禁通过前，不应把隐式业务对照的差异归因于 Skill 内容。
