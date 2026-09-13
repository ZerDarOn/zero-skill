# Round 31 冻结前独立复核

日期：2026-09-14

复核对象为 `prose-polish-current-humanizer-24` 的协议、六题、准备器输出测试，以及当前 `prose-polish` 与固定 Humanizer 包。复核任务没有修改文件。

## 首轮发现

首轮发现两项 P2：

1. 原 `rescheduled-consultation-window` 与活动用例 `preserve-reschedule-relation-under-limit` 都是旧时间改到新时间、访问细节不变、已确认者免确认、仅新时间冲突者在截止前回复的模板；新题 90 字上限还比用于 0.1.3 修订的 75 字更宽，不能作为独立前向表面。
2. 测试虽然核对了生成提示和两套 Skill 副本，却没有读取 `prepared/promptfooconfig.json`；若准备器改错模型、工作目录、沙箱、网络、宿主集成或测试路径，冻结测试仍可能通过。

## 修订

第一题改为 `scoped-migration-plan-under-limit`：在 85 个 Unicode 字符内保留东区和北区的当前范围、南区带日期的兼容性条件、西区明确排除、名单未定，以及计划不等于上线承诺。可行参考为 72 个字符；测试同时锁定它不复用旧改期题的关键结构。

准备测试新增生成配置与测试清单的确定性 SHA-256，并逐字段核对三臂 label、相同模型与推理等级、各自 fixture 工作目录、只读沙箱、never approval、网络与网页搜索关闭、进程环境不继承、apps/plugins/multi-agent 关闭、隔离 HOME/CODEX_HOME/USERPROFILE，以及 `tests.json` 路径。当前包和上游包在仓库源、prepared skill 与实际 `.agents/skills` fixture 三处均做逐文件和包指纹核对。

## 复核结论

修订后无开放 P0–P3。六题保持三个机制各两题；字符上限可行，硬标准与核心标准可观察，没有把主观审美偷渡为唯一答案。ours-versus-baseline 门槛、upstream context-only 角色、rubric 隔离、Humanizer 固定提交与 MIT 来源边界均一致。

冻结前专项测试 6/6、`validate_collection.py` 与 `git diff --check` 通过。该结论只授权冻结协议，不是行为质量结果。
