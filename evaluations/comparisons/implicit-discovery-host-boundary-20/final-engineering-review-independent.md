# Round 27 最终独立工程审查

日期：2026-09-13

## Findings

未发现未解决的 P0–P3。发布候选的公开机器报告可以从冻结协议和本机 ignored raw 正式运行逐条重算；文档保持了路由选择、正文加载、策略阻断、传输完整性和回答质量之间的边界。零容忍门禁失败后没有运行业务 Skill 隐式质量对照，也没有修改 Skill、版本、catalog、evidence 或活动用例。

## 报告与 raw 重算

本机正式目录 `implicit-discovery-host-boundary-20-formal-20260913-v1` 存在。独立读取冻结协议并重新调用 normalizer 与 analyzer 的分类函数，得到 12 条互异 trajectory、12 条公开投影、2 个 arm 汇总、6 条 incident、完整 gate 和 decision，均与 `evaluations/reports/implicit-discovery-host-boundary-round-27.json` 逐项相等。

原始制品与报告保存的 SHA-256 一致：

- `frozen.json`：`d72c2deafcf3279befc5843b763bb56b7996a62bae119de127295f2ca89b544b`
- `run-meta.json`：`d345b48b9bf72bd77ba49dc09d8fff8157869ab6759e3622317abcc80a8e9852`
- `native-results.json`：`4e6679834b8785d572ebf901fa4258548dfe65d4f8777f9f33ad546135e56884`
- `implicit-discovery-analysis.json`：`1345dc99585202160381c0e1d132db08b83837f30469e09dde8f151e0f687e29`

正式运行的 12 个 trajectory 目录与 2 题 × 2 臂 × 3 次的冻结任务全集相等，没有缺失、未知或重复项。seed `270913` 重算的提交顺序逐项等于 `run-meta.json`，顺序 SHA-256 为 `044491b1b4aaa1062f7c3953c7a12ce9db27f688ad4e7dae06abcc00cd05a86f`。公开报告中的开始时间、结束时间、时长、重复数、worker 数、预期与实际轨迹数、有效与无效轨迹数及回合数也与 raw metadata 相等。

prepared prompt 在两臂间逐字相同，不含 probe Skill id、`.agents/skills/` 路径或正文令牌。baseline fixture 为空；probe fixture 只含目标 `SKILL.md`，包指纹 `e45999851a3cf7d3dbb061b784c7a82bb5a9b7bfd6448751ecf2414ef8670887` 与协议和报告一致。protocol、spec、cases 及 preparer、runner、normalizer、analyzer 的当前哈希均符合冻结绑定。

## 分类与决定

独立重算结果为：

| 臂 | 尝试 | route selected | body loaded | policy blocked | transport valid | operational success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 6 | 0 | 0 | 0 | 6 | 6 |
| probe | 6 | 6 | 0 | 6 | 0 | 0 |

probe 的 `route_selected=6/6` 仅来自 stderr 中同时存在 `exec_command failed` 和边界完整的精确目标 Skill 路径，表示模型选择并尝试该路由。六条最终输出均为备用值而非正文令牌，所以 `body_loaded=0/6`。六条 stderr 均有策略阻断；每条还存在两条 agent message 和 output-last 绑定失败，因此 `transport_valid=0/6`。失败轨迹全部保留在 outcomes 和 incidents，没有被 runner 的基础技术失败过滤。

门禁重算为 `passed=false`：baseline 五项失败计数均为 0；probe 路由缺失为 0，正文加载失败、策略阻断和传输失败各为 6。报告据此正确写入 `business_comparison_authorized=false`、`business_comparison_run=false`、`infrastructure_investigation_opened=true` 和 `skill_change_authorized=false`。scope 同时记录 `business_trajectories=0`，本机正式运行之后也没有 Round 27 业务运行目录。

## 投影与状态防护

对 `scope`、`experiment`、`analysis`、`decision` 和 `limitations` 重新执行 canonical JSON SHA-256，结果为 `b5e8ed1ac1291e090063a22d31160b9ae0024c797ac958793e1bef9fbb35dc4c`，与报告的固定投影一致。报告回归测试会重新绑定协议、基础设施、spec、cases、probe 包、raw artifact、两份独立复核、轨迹投影、arm 汇总、门禁和决定。对轨迹正文加载值、gate pass、运行后复核哈希或业务授权决定进行修改，并同步重算报告内投影，仍会被固定预期和语义断言拒绝。

相对冻结提交 `6cb20962d7ee679da829278434d07a35d3a5a101`，`skills/`、`catalog/` 和 `evaluations/cases/` 没有差异。当前 catalog 仍有 16 个 `experimental` Skill，活动用例总数仍为 148。

## 文档边界

`README.md`、`evaluations/README.md`、`docs/quality-polish-round-27.md` 和 `formal-results.md` 均把 6/6 描述为精确路径读取尝试或路由选择，并明确同时报告正文加载 0/6。它们没有把路由选择写成成功读取正文，没有评分回答质量，也没有把宿主策略失败解释成业务 Skill 退化。公开材料一致说明业务比较已停止，Skill 与 catalog 未变。

## 验证

- Round 27 定向测试：17/17 通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：158 项通过；1 项因当前 Windows 环境没有创建符号链接权限而跳过。
- `git diff --check`：通过。
- 独立 raw 重算：12 条 trajectory projection、arms、incidents、gate、decision、任务顺序、目录全集、运行元数据和四项 artifact hash 均一致。

## 限制

本审查确认的是当前仓库字节与本机 ignored raw 的一致性、分类边界和发布论断，不把 SHA-256 当作外部签名或可信时间戳。结论只覆盖当前主机、原生 CLI、项目级隐式安装、只读沙箱、`gpt-5.6-sol` medium 和两个合成触发表面。精确路径尝试仍不证明文件读取或正文加载；本轮没有业务质量样本，因此不能推断任何业务 Skill 的隐式触发质量或回答质量。
