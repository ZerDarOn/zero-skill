# 第四次吸收：产品背景简报与文章配图规划

日期：2026-09-09。起始提交：`fd653fe378006a2f3815593ee610f85b3a5c3a0e`。

## 来源与取舍

| 上游固定来源 | 采用 | 舍弃 | 本地规则与可观察用例 |
| --- | --- | --- | --- |
| Marketing Skills `5b2c0007766c6a1cf1d53fd8fc73e979e0821022` 的 `product-marketing/SKILL.md`；仓库 MIT 许可，固定目录无许可覆盖 | 共享产品背景、购买角色分离、保留客户原话与修订历史 | 硬编码 `.agents`、自动读取或保存、固定问卷模式、自动版本递增 | 区分当前能力、路线图、证据、内部想法和未知项；四个 product 用例 |
| Baoyu Skills `6b7a2e417500561a5ecdd0b168332f4142584617` 的 `baoyu-article-illustrator/SKILL.md` 及规划相关引用；仓库 MIT 许可，固定目录无许可覆盖 | 先找有信息价值的位置、说明目的、先定结构再定风格、按需写完整提示词 | 图像生成、后端选择、配置、复制素材、保存提示词和自动修改文章 | 保留节点、数据和不确定性，只做规划或提示词；四个 visual 用例 |

两个包均为本仓库原创措辞，没有复制第三方文件、运行上游脚本或接入生成后端；`catalog/upstreams.json` 保持 `imported: false`。审查层级只提升到相应固定入口及上述必要引用，不冒称完成整仓审查。

## 实现

- `product-context-brief` 0.1.0：`productivity / workflow`。根据用户用途整理产品、角色、证据、替代方案、计划与未知项；保留有限样本和更正关系，不自动写入工作区。
- `article-visual-plan` 0.1.0：`creation / workflow`。只在有助理解的位置规划配图，先描述信息结构与关系；用户明确要求时才给完整生成提示词，本批不生成图片。

两者均保持 `experimental`、`evidence: null`。单次合成对照与执行者评分不能支持 `verified`。

| 技能 | 包 SHA-256 | active 用例 SHA-256 |
| --- | --- | --- |
| `product-context-brief` | `f821cb134112decd46c07b8b50d5fef7e03c4bbae91d6af68344e45552dbc4c5` | `db2fa9651062441e5e918204f42b02635078a5485a5c92b0275fac9d8e92f81a` |
| `article-visual-plan` | `e02fed142a73421a2cc091bfea0d6faefef4c8035e671d4866e65708e9973a87` | `6ab2213a5d82b442152b0260e2d8e9550c615f5cf68a8f2c8779df0a9212b4f5` |

## 对照运行

先在技能文件不存在时运行 8 个 `planned` 合成用例，再实现、登记并只把 `stage` 改为 `active`，随后用相同 8 个用户请求显式加载对应完整包。模型为 `gpt-5.6-sol`、`medium`。共 16 次有效单轮生成，模型启动 16 次、启动失败 0、重试 0；每次使用独立临时目录、`--ephemeral --ignore-user-config`、只读沙箱且无工具。

| 技能 | Baseline 全约束 | Skill 全约束 | 核心任务 | 严格改善 | 退化 |
| --- | --- | --- | --- | ---: | ---: |
| `product-context-brief` | 2/4 | 4/4 | 3/4→4/4 | 2 | 0 |
| `article-visual-plan` | 4/4 | 4/4 | 4/4→4/4 | 0 | 0 |

product 的两项全约束改善分别来自：保留给定的客户引语来源 ID；不把预算复核条件句扩写成产品需求。前一例中 baseline 已正确区分内部定位设想与现有能力，后一例也已满足“最终决策者或付款方尚未确认”的冻结要求，不能把这些算作额外改善。baseline 与 skill 都通过了限定范围更新和四要点短答。

visual 的四例两组均通过：都选择了流程与比较位置、保留定性不确定性、只改指定视觉、并完整遵守显式流程图关系。这个结果没有显示该包优于强 baseline，但确认本次输出没有在冻结边界上退化。

baseline 总观察时长 113,196 ms，输入／缓存输入／输出／推理 token 为 122,060／94,464／1,496／52；skill 为 118,375 ms 和 128,012／102,400／1,810／215。时长是本地编排观察区间，不是服务端延迟。

完整包、前后用例快照、精确提示、原始输出、事件、stderr、哈希、时长、用量，以及每项 `must_include` 与 `must_avoid` 的独立判断和依据，见[诊断证据](../evaluations/reports/fourth-absorption-0.1.0-diagnostic.json)。

## 本地导出

两个 ZIP 都只包含 `bundle-manifest.json` 和对应 `SKILL.md`；manifest 包指纹与实现表一致。

| 归档 | ZIP SHA-256 |
| --- | --- |
| `dist/product-context-brief-0.1.0.zip` | `086f67c8680fcf98b523e99be03ab02317c1f79957168af5513145e74793a486` |
| `dist/article-visual-plan-0.1.0.zip` | `08850217e4eb3b720fd96f5398db3c3cbd6b915904ebfbf7d2aadd7d974aa79f` |

## 限制

每例只运行一次，初评由本次执行任务中的 Codex 完成，后由同项目 Astra 只读复核并修正一项过严的子项判定；这仍不是独立人工评审或重复采样。显式加载不测试自动发现与路由；无工具隔离 CLI 不代表真实市场研究、团队工作区集成、图像生成质量或开放工具环境安全。强 baseline 已按全部冻结约束通过 6/8；观察到的两项改善不能证明稳定或聚合收益。

`choose-informative-positions` 的用户请求只写“最多 2 张”，但两条冻结 `must_include` 同时强制 P2 和 P4，形成了不必要的隐藏固定组合。现有两组都输出两张，因此 4/4→4/4 不变；该例只能证明当前两张方案符合这套狭窄标准，不能证明技能普遍尊重一张或两张的自由选择。后续版本应接受一张或两张有效位置，或把同时覆盖两种关系明确写进用户请求；本批保留原始冻结用例与快照，不静默改写。
