# Round 32 冻结前独立复核

日期：2026-09-14

## Findings first

初审发现两项 P2，均已在冻结前修复。复核后 **无开放的 P0–P3 发现，可以冻结**。

### [P2] feature flag 题的结果分支不能唯一判定

初版 `flag-cohort-confounded-by-payload-size` 只要求说明“三种可能结果”，但同一合成 payload 的 flag 开关对照存在四种结果。隐藏标准后验选取“仅开启失败、两者都失败、两者都不失败”，遗漏“仅关闭失败”，题面没有给出选择前三种的依据。不同答题者即使做出完整而合理的三分支分析，也可能因选择不同而被扣分。

**修复：** 题面改为明确要求分析四种开关组合；硬标准增加“仅关闭失败”的反常分支，要求先复核 flag 身份、实验控制或随机波动，不能把它归因于新解析器。机制、arm、核心标准索引和 decision gate 均未改变。`cases.json` 与 prepared tests 的固定哈希已随之更新。

### [P2] 组装包的“自包含”表述掩盖了两个后续 sibling-skill 调用

初版 provenance 把运行夹具称为自包含 project skill。包内 `SKILL.md` 的三个同目录 Markdown 引用及其脚本/TypeScript 下游引用确实全部闭合，但原文在修复和完成验证阶段还要求调用 `test-driven-development` 与 `verification-before-completion` 两个 sibling skills；本运行包没有安装它们。由于本轮任务只停在只读诊断建议，不会进入修复或完成验证阶段，这不破坏共同测试切片，却需要明确披露，避免把局部引用闭包说成完整上游工作流。

**修复：** README 与 provenance 现在区分“同目录文件引用闭合”和“后续 sibling skills 未组装”；明确本轮只测试只读诊断切片，不能外推到完整 Superpowers 流程。第三方源文件字节未修改。测试新增同目录引用闭包及 sibling 边界断言，包指纹随 provenance 更新。

## 题目与门槛复核

- 六题均为当前 Skill 完成后的新合成表面，ID 与冻结前 13 个活动用例不重复。文本相似度和人工语义对照确认，它们没有复用 Round 22 的具体日志、实体或数值；虽然继续测试证据覆盖和因果拆分等能力，但触发分别换成 200 空结果、完成态查询、索引与超时捆绑、flag 与 payload 完全混杂、retry attempt 和 process boot 身份。
- 三个机制各两题，每题四项硬标准，`core_criteria=[0,1,2]` 均为有效且不重复的零基索引。gate 只比较 ours 与 baseline，要求同机制两题各自达到预注册失败次数并保持 54 份输出有效；upstream 为 context-only，触发只允许打开最小候选设计。
- 题面提供了隐藏标准使用的全部事实、身份字段、缺失证据和结果分支。硬标准判断可观察的结论、事实保留、检查选择、分支解释与禁止行为，没有要求特定措辞或审美偏好。
- 格式限制可行：Android 题可以在两句内同时给结论和唯一复验检查，满足“不超过三句”；session/boot 题存在恰好两句的完整答案见证。索引/超时题可用严格两项有依赖顺序的编号检查；其余题均只要求一项检查。格式没有迫使答题者删除核心关系。

## 三臂与运行隔离

- 三臂使用同一模型、medium、公共任务提示、只读 sandbox、禁网、禁 web、`approval_policy=never`、隔离 Git 工作区与隔离 HOME。apps、plugins 与 multi-agent 均关闭。baseline 没有 Skill；两个 Skill 臂只增加对各自固定项目 Skill 的显式调用前缀。
- 公共提示禁止工具、文件与外部系统，并要求把检查写成未执行状态。六题只比较材料内的诊断建议，因此当前 Skill 与上游在共同能力范围内对称；上游更广的复现、改码、TDD 和完成验证流程不计入本轮结论。
- 准备测试锁定完整 `promptfoo.json`、`cases.json`、prepared config/tests、三臂 provider 全字段、每一行 metadata 和 `prefix + common_prompt + source prompt` 的精确组成。hard criteria 与 core indexes 不进入 agent prompt。
- 预备产物为 18 行，正式计划为 `6 × 3 × 3 = 54` 份输出。失败保留、不重试；协议未给 upstream 结果或总体分数触发改版的入口。

## 上游来源、字节与安全边界

- 固定来源为 `obra/superpowers@b36e0829c6d0140e93cfef2ca599b1b07d4a7797`，许可证为 MIT。组装包含 LICENSE、SKILL、三个同目录 Markdown 资源、一个 TypeScript 示例和 `find-polluter.sh`。
- 七个第三方文件逐字等于原固定 fixture，并同时匹配原 fixture provenance 与 Git blob；全部为 LF。布局变化只把 `skills/systematic-debugging/` 的内容复制到运行包根，并加入仓库 LICENSE。组装说明保存在原创 `provenance.json`。
- `SKILL.md → root-cause-tracing.md → find-polluter.sh`、`SKILL.md → condition-based-waiting.md → condition-based-waiting-example.ts` 以及 `defense-in-depth.md` 的同目录引用全部存在。脚本只作为文本资源复制；协议禁止工具执行，准备过程只复制字节，专项测试没有运行上游脚本。
- 新增题目和运行材料均为合成内容。扫描未发现本机绝对路径、用户名、访问密钥或真实账户资料。

## 固定指纹

- `promptfoo.json`: `71d0d8c472e081d7691368ceb8c19aa3270fef29d90ca293caa93e9c2180d20d`
- `cases.json`: `9ab66e760df491dd34b2826aea5a3ec0e1cd320eeb11e254d9fb04fb7b5e7d18`
- prepared config: `709aab6bed1937447377994734afdd0449f12f68ddb83b9a449c7daa3a21d8a3`
- prepared tests: `573cd8f3a58b56863f9ea0b4cfd3a36dfa0942bb2a414e206e7865de4379b0cb`
- current Skill package: `5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72`
- assembled upstream package: `17c82641ac6528efd6c1728206442de6ca345314a176a8448c351191b35ca731`

## 修改范围

本复核只修改了比较题目/说明、组装夹具的原创 provenance、冻结设计测试，并新增本复核记录。没有修改 `skills/engineering/debug-evidence-triage`、`catalog/collection.json` 或活动用例。

## 验证命令

```powershell
python -m unittest tests.test_debug_current_systematic_comparison -v
# 5 tests，全部通过

python scripts/validate_collection.py
# PASS

git diff --check
# 通过，无输出
```

另以只读脚本比较组装包与原 fixture 的逐文件 SHA-256/Git blob，递归检查同目录引用闭包，扫描 UTF-8/LF 与隐私模式，并构造满足三句、两句及检查数量限制的答案见证。

## 剩余限制

- “未参与当前 Skill 编写”由提交时间、当前 Skill 字节未变、冻结前活动 ID 集和题面差异支持；它不是对模型训练语料未知性的证明。
- 严格格式与语义标准虽然存在可行答案，正式评分仍需逐候选判断，不能用字符串计数替代语义盲评。
- 该对照只覆盖六个合成、单轮、只读诊断任务和显式 Skill 调用。它不验证真实系统访问、实际复现、改码、测试执行、隐式发现或完整 Superpowers 工作流。
