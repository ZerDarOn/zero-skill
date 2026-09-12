# 第二十一轮最终独立工程复审

## 结论

**原两项 P2 与一项 P3 均已关闭；未发现新的 P0–P3 问题。修订内容可以进入最终提交。**

提交前需重新暂存最新修订：当前 `docs/quality-polish-round-21.md`、机器报告和 Round 21 测试相对原暂存版本显示为 `AM`，两份最终独立工程评审文件仍为未跟踪文件。这是 Git 交付状态，不是内容缺陷。

## Findings

无剩余 findings。

## 原发现关闭情况

### 已关闭 P2：用户专属绝对路径

- `docs/quality-polish-round-21.md` 与机器报告均改为 `$CODEX_HOME/skills/repo-conventions/SKILL.md`。
- 暂存补丁相关文档、报告和两份工程评审中已检索不到用户专属 home 路径。
- 原 `final-engineering-review-independent.md` 也已在入库前脱敏，并明确注明“路径在入库前脱敏，原发现语义不变”。历史 finding 仍保留，修复事实可审计。

结论：账户信息泄露和跨机器路径不稳定问题已消除。

### 已关闭 P2：评阅者方法身份未完整进入投影

`reviewer_projection()` 现在包含：

- `model`
- `reasoning_effort`
- `independent_human`
- `note`

连同原有的 arm mapping 盲性、既往协议／Skill 暴露、文件访问边界、意外读取文件及偏差说明，这些字段同时进入 decision projection 与 evidence projection。

测试新增直接断言：评阅模型为 `gpt-5.6-sol`、推理等级为 `medium`、`independent_human: false`、note 非空；并新增把模型改为 `different-model`、把 `independent_human` 改为 `true` 的负向变异。两种变异均会使证据投影哈希不同。

新的 decision projection SHA-256 为：

`ee69dc7b83f16f3b8b321e431152f2590b04dc0ec25b0ab470a241cb6fa4341a`

该值可按 canonical JSON 规则从当前机器报告复算，并与测试常量一致。

结论：模型辅助评审不能被静默改写成独立人类评审，模型、推理等级和 reviewer note 也已受投影保护。

### 已关闭 P3：prepared/artifact 哈希不属于 evidence root

证据投影已升级为 `round21-evidence-projection-v2`，新增绑定：

- 实验模型与推理等级；
- `prepared_hashes`；
- 八个 `artifact_hashes`。

机器报告新增 scope，明确 evidence v2 覆盖冻结提交、模型配置、source/prepared/raw artifact hashes、评阅方法与偏差、匿名映射、输出哈希、评分和偏好。测试增加 prepared tests 哈希与 `results.json` artifact 哈希的负向变异；任一变化都会改变 evidence root。

新的 evidence projection SHA-256 为：

`bfd195f4b80c331dd8d9836a6dffb7399938061a7fe28b417e85bb4f2e29e41f`

该值可从当前报告按 v2 投影重算，并与测试常量一致。

结论：投影范围已与报告声明一致，原低优先级完整性空档关闭。

## 回归核对

修订只改变路径表示、投影字段、投影版本与哈希常量，没有改变冻结题面、36 份输出、144 个布尔评分、匿名 arm 映射、总分或候选门槛。

- baseline 仍为 67/72、13/18 完整、偏好 3；
- 0.1.2 仍为 70/72、16/18 完整、偏好 5；
- 平局仍为 10；
- 来源核心错误仍为 `0/0`、`0/0`、`2/0`；
- 行动角色两题仍均为 `0/0`；
- bounded 仍为 `0/0`、`eligible: false` 且只作诊断；
- 候选门槛仍未触发，保持 0.1.2。

## 验证记录

- `python -B -m unittest tests.test_person_evidence_natural_context_round21 -v`：3 项全部通过。
- 未重复运行全仓测试；上一轮完整复核已记录 74 项中 73 项通过、1 项因 Windows 符号链接权限跳过。
- 本复审没有修改已有产品、协议、报告或测试文件；除按要求脱敏原工程评审外，只新增本复审文件。

## 最终判断

**可以在重新暂存最新修订和两份工程评审后提交。** 流程偏差仍被准确披露，arm mapping blindness 的结论没有被扩大；单模型、显式调用、非独立人类评审等限制均受 v2 证据投影保护。
