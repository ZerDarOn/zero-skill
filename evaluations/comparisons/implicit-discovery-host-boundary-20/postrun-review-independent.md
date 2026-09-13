# Round 27 独立运行后复核

日期：2026-09-13

## Findings

未发现未解决的 P0–P3。冻结协议、正式 ignored raw run 与保存的 `implicit-discovery-analysis.json` 相互一致；门禁失败和停止业务隐式质量比较的决定成立。本次复核没有修改任何已有文件，只新增本记录。

## 冻结与原始证据绑定

正式运行基于冻结提交 `6cb2096`，模型为 `gpt-5.6-sol`、medium，重复数为 3，任务顺序种子为 `270913`。独立重算得到：

- protocol：`15c45a914b63ac76b25e373ec3245190512a5050aeca15399e3c06fa16e6be56`
- spec：`369a5d85e1d8959a186e02ec734c2ee85ede9487f6e08bb0aab7df0e56be43b3`
- cases：`d22f5d4050155170d7990f479a6324754e311f82627a06b374082a59670547fd`
- prepared config：`904151fc5d58c7bdcd357467f2caee7778b790c7760b7a5f95d777def0fc20e3`
- prepared tests：`7536e6b6d6555351a4419c7f92bed4d2c6e60fcf2c9d1d37590e8eb0c493d584`
- probe package：`e45999851a3cf7d3dbb061b784c7a82bb5a9b7bfd6448751ecf2414ef8670887`
- `frozen.json`：`d72c2deafcf3279befc5843b763bb56b7996a62bae119de127295f2ca89b544b`
- `run-meta.json`：`d345b48b9bf72bd77ba49dc09d8fff8157869ab6759e3622317abcc80a8e9852`
- `native-results.json`：`4e6679834b8785d572ebf901fa4258548dfe65d4f8777f9f33ad546135e56884`
- `implicit-discovery-analysis.json`：`1345dc99585202160381c0e1d132db08b83837f30469e09dde8f151e0f687e29`
- job order：`044491b1b4aaa1062f7c3953c7a12ce9db27f688ad4e7dae06abcc00cd05a86f`

protocol 绑定的 preparer、runner、normalizer 与 analyzer 当前字节均符合冻结哈希。baseline fixture 为空；probe fixture 只含 `.agents/skills/implicit-discovery-probe/SKILL.md`，文件哈希与冻结清单一致。两题在 baseline 与 probe 的 prepared prompt 逐字相同，且均不含 Skill id、`.agents/skills/` 路径或两个正文令牌。

## 队列完整性

两题、两臂、三次重复展开为 12 个互异 trajectory id。`run-meta.json` 保存的 12 项提交顺序与冻结种子重算结果逐项一致；`native-results.json`、12 个轨迹目录和冻结任务全集完全相等，没有缺失、未知或重复项。每条轨迹只有一个生成回合，未发现补跑、失败筛选或跨目录拼接。

runner 的基础技术结果为 baseline 6/6 有效、probe 0/6 有效，合计 6/12；该差异没有被分析器当作质量结果，也没有丢弃失败轨迹。全部 12 条都进入最终 outcomes，6 条 probe 失败全部进入 incidents。

## 分类独立复算

使用冻结 analyzer 的 `normalize_trajectories`、`classify_trajectory`、`summarize_outcomes` 与 `build_gate` 只读重算，所得 arms、12 条 outcomes、6 条 incidents、gate 和 decision 与保存的联合分析对象完全相等。

| 臂 | 尝试 | route selected | body loaded | policy blocked | transport valid | operational success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 6 | 0 | 0 | 0 | 6 | 6 |
| probe | 6 | 6 | 0 | 6 | 0 | 0 |

baseline 六次都严格返回 `ROUTE-NOT-AVAILABLE`，没有选择目标路由、泄漏正文令牌、策略阻断或传输错误。probe 六次都在 stderr 中留下边界完整的 `.agents/skills/implicit-discovery-probe/SKILL.md` 精确路径与 `exec_command failed`/`blocked by policy` 证据，因此 `route_selected=true`、`policy_blocked=true`；最终输出均为备用值，没有任一正文令牌，故 `body_loaded=false`。每条 probe 轨迹都有两条 agent message，output-last 只对应后一条，因此同时记录 `agent-message-count-failure` 与 `output-binding-failure`，`transport_valid=false`。这些字段分别描述路由选择、正文加载、策略阻断和传输完整性，没有把选择尝试误写成加载成功。

## 门禁与决定

零容忍门禁独立重算的 baseline 五项观测均为 0；probe 路由选择失败为 0，正文加载失败、策略阻断和传输失败各为 6。后三项超过冻结上限 0，因此 `gate.passed=false`，诊断状态为 `route-selected-load-blocked`。

保存的决定正确设为：`business_comparison_authorized=false`、`infrastructure_investigation_opened=true`、`skill_change_authorized=false`。本轮只定位自然提示下的宿主读取边界，不评分回答质量，不授权修改业务 Skill、版本、catalog、evidence 或活动用例；按冻结协议必须停止，不开展后续业务隐式质量比较。

## 验证命令

- `python -m unittest tests.test_implicit_discovery_analysis tests.test_implicit_discovery_round27 -v`：13 项通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：见最终验证记录；除当前 Windows 环境无法创建符号链接的既有跳过外无失败。
- `git diff --check`：通过。
- 独立只读重算脚本：12 条 outcomes 与保存分析完全相等，12 个轨迹目录与冻结任务全集完全相等，prepared prompts 同臂逐字一致且不含 Skill id、路径或令牌。

## 限制

本结果只覆盖当前主机、原生 CLI、项目级隐式发现、只读沙箱、单模型和两个合成触发表面。精确路径证据能说明模型选择并尝试了目标路由，不能证明文件读取或正文加载成功。策略阻断发生在宿主边界；本轮没有尝试无沙箱绕过，也不能据此推断其他主机、安装方式、沙箱配置或未来版本的行为。
