# Round 31 最终独立工程复核

日期：2026-09-14

## Findings first

**无开放的 P0–P3 发现，可提交。** 本次终审没有修改业务 Skill、评分、协议、catalog 或活动用例，也没有发现需要修复的工程问题。

公开机器报告可以从本机保留的匿名包、盲态评分、揭盲映射、评分汇总和运行摘要逐项重建；在没有 ignored raw run 的新 checkout 中，固定证据投影与已提交冻结来源仍可校验报告。测试同时锁定固定投影、raw 制品哈希、冻结提交字节、门槛语义和运行配置，协调修改报告与门槛、运行状态、重复次数、prepared 题目或实际 Skill 副本都会被拒绝。

## 核验结果

- 从 `blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json` 与 scored review 连接 18 个 `review_id`、54 份输出和 216 个布尔判断，重算得到 baseline `71/72`、ours `70/72`、upstream `69/72`；完整输出依次为 `17/18`、`16/18`、`15/18`；唯一偏好依次为 `1/0/0`。
- 六个 `false` 均位于 `restrained-voice-with-fixed-closing` 的第三项标准。该题核心失败为 baseline `1/3`、ours `2/3`、upstream `3/3`；其余五题三臂均为 `0/3`。公开报告中的逐题计数与原始盲评一致。
- 三个冻结机制门槛均未触发。`author-voice-restraint` 中 ours 的两题为 `2/3` 与 `0/3`，没有满足“两题各至少 2/3”的预注册条件；upstream 保持 context-only，不参与本地改版决定。候选设计保持关闭。
- `run-meta.json` 记录一次 validate 和一次 `--repeat 3 --no-cache` eval；正式运行 expected/result/passed 为 `54/54/54`、failed 为 0。summary 中三臂各 18 行，provider error、forbidden tool row 和 Promptfoo failure 均为 0。预检三臂各一行，只作基础设施验证，不计分。
- 冻结提交 `5fb4a1ca09a7a17059b41a372daf1c06e0927fa0` 是当前 HEAD 的祖先且包含于 `origin/main`。从该提交读取的协议、题目、当前 `SKILL.md` 与 Humanizer provenance 的 Git blob 哈希分别匹配公开报告；冻结文件、prepared config/tests、正式制品和 preflight summary 的哈希也一致。
- Humanizer 固定于提交 `9862685f575c65a8247f90369951df1b3416e3d6`。`LICENSE`、`SKILL.md` 与 `agents/openai.yaml` 均匹配 provenance 的逐文件 SHA-256；MIT 许可证随包保留，包指纹为 `1f7cf25aac13904bfa2a9e1f54f83ba8f620c50bd059b2f7b634e62d7010adde`。运行只使用 `SKILL.md`，host metadata 未作为提示内容。
- 六道冻结题的 prompt 原样加入活动用例；`prose-polish` 活动用例从 9 增至 15，全仓从 160 增至 166。Round 30 历史测试只将固定总数改为“不低于当轮报告的 160”，允许后续轮次增长但仍拒绝回退到 160 以下；Round 31 测试固定当前总数 166。
- `skills/` 与 `catalog/` 无工作树差异。`prose-polish` 仍为 0.1.3、`experimental`、`evidence: null`，当前包指纹仍为 `85460012946903fe6401f8df5f6b284497103606fbeaed86eda963d92a103047`。
- README、评测索引、Round 31 文档与机器报告没有把模型辅助匿名评阅写成人工审计，也没有声称当前 Skill 优于 baseline 或 Humanizer。公开新增材料使用合成任务，报告未发现本机绝对路径、用户名、密钥样式或真实人物资料；检查文件均为 UTF-8/LF。

## 本次修复

无。终审只新增本复核记录。

## 剩余限制

- 匿名评分与揭盲后决策复核由同一个模型辅助任务完成；评分时对 arm mapping 保持盲态，但这不构成第二位独立人工评审。
- 结果仅覆盖六个合成、单轮、中文、显式项目级调用任务，以及一个模型和推理等级；不能外推到真实作者满意度、隐式发现、多轮或文件编辑、发布、其他语言和一般产品排名。
- Promptfoo raw run 仍被 Git 忽略。提交后的公开报告包含合成输出、评分投影与制品哈希，可在新 checkout 校验固定证据，但无法仅凭仓库重建 provider 事件与运行时成本。

## 验证命令与结果

```powershell
python -m unittest tests.test_prose_round31 tests.test_prose_current_humanizer_comparison tests.test_article_visual_round30 -v
# 20 tests，全部通过

python scripts/validate_collection.py
# PASS

python -m unittest discover -s tests -v
# 218 tests，全部通过；1 个与本轮无关的环境性 skip

git diff --check
# 通过，无输出
```

另以只读 Python 脚本完成匿名评分链、逐题核心失败、机制门槛、运行成本百分比、活动用例计数、包指纹和隐私模式的独立重算；以 `git show <freeze_commit>:<path>` 核对冻结 Git blob，而非依赖工作树换行转换后的字节。
