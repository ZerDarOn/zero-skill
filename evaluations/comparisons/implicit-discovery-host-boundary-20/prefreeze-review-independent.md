# Round 27 独立冻结前复核

日期：2026-09-13

## 结论与发现

按当前候选字节复核，未发现未解决的 P0–P3。建议冻结当前 protocol、analyzer、spec、cases、probe 包及三项运行基础设施，然后按冻结的 12 条队列执行一次正式运行。正式运行应保留所有失败；门禁失败时只能记录宿主边界并停止业务隐式质量对照。

复核过程中曾发现并报告以下问题，均已在本次结论所依据的最终字节中关闭：路由证据可被正文或近似路径误触发、读取命令可携带 shell 组合操作、空输出未计入传输失败、baseline 传输或策略失败未关闭门禁，以及缺少 `exit_code` 的命令仍可能被视为成功。对应负向测试现已覆盖这些边界。

## 证据分层

- `route_selected` 只接受两类证据：结构化 `command_execution` 中指向精确 `.agents/skills/implicit-discovery-probe/SKILL.md` 的命令，或同一 stderr 行同时包含 `exec_command failed` 与该精确路径。普通 agent message、`.bak` 后缀和粘连前缀不构成路由证据。这个字段证明模型选择并尝试了目标路由，不证明读取成功。
- `body_loaded` 只在最终输出严格等于该题冻结令牌时成立；路由尝试、stderr 路径或过程消息不会替代正文加载证明。
- `policy_blocked` 单独由 stderr 的 `blocked by policy` 标记计算，并分别进入 baseline 与 probe 的零容忍门禁；它不被混入 `transport_valid`。
- `transport_valid` 独立检查 setup、单回合、exit/error、JSONL、thread 绑定、唯一 `turn.completed`、单一 agent message、output-last 绑定、非空输出、禁用 item 以及命令边界。probe 唯一允许的成功命令必须完整匹配窄读取形式，且 `status=completed`、`exit_code=0`；`;`、管道、`&`、换行、重定向、反引号和 `$(` 等组合符都会使传输失败。baseline 不允许任何命令执行。

## 冻结内容独立重算

- protocol SHA-256：`15c45a914b63ac76b25e373ec3245190512a5050aeca15399e3c06fa16e6be56`
- analyzer SHA-256：`802d18bddd6142486ce2cf077043614c290ec998c7940b1573c244ffe9f8098e`
- preparer SHA-256：`4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`
- runner SHA-256：`cac3e238d717f7a268d9b6800bec11002eaa5d3e54ddf2458f65a2983e9912b5`
- normalizer SHA-256：`91c336bc71b409adabe8c39668cbbb98b72fcb6bafcfc05c21faf899455daa9d`
- spec SHA-256：`369a5d85e1d8959a186e02ec734c2ee85ede9487f6e08bb0aab7df0e56be43b3`
- cases SHA-256：`d22f5d4050155170d7990f479a6324754e311f82627a06b374082a59670547fd`
- probe package SHA-256：`e45999851a3cf7d3dbb061b784c7a82bb5a9b7bfd6448751ecf2414ef8670887`

两题、两臂、三次重复独立展开为 12 个互异 trajectory id。用冻结 seed `270913` 重算的顺序 SHA-256 为 `044491b1b4aaa1062f7c3953c7a12ce9db27f688ad4e7dae06abcc00cd05a86f`。正式 analyzer 同时要求 `frozen.repetitions=3`、`run-meta.repeat=3`、完整 trajectory 集合及上述确定性乱序。

当前 preflight 的 prepared config 与 tests SHA-256 分别为 `904151fc5d58c7bdcd357467f2caee7778b790c7760b7a5f95d777def0fc20e3` 和 `7536e6b6d6555351a4419c7f92bed4d2c6e60fcf2c9d1d37590e8eb0c493d584`。逐题读取 prepared prompt 后，两臂字节相同，且不含 probe Skill id、`.agents/skills/` 路径或两个正文令牌；两题 prompt SHA-256 分别为 `3c67e1a0f52b9f0bd7d8bc98acfb81b0be354f16e79f5542aeed8e4746b7bacb` 和 `4e124e9ab695fb188e183ff411031ed612d7e512de6240dfea6ca2d7599c3a35`。baseline fixture manifest 为空，probe manifest 只含目标 `SKILL.md`。

## Raw 证据复核

探索运行 v4、v5、v6 的 `frozen.json`、`run-meta.json` 和 `native-results.json` 三组 SHA-256 均与 `preflight-validation.md` 一致。命令记录也支持文档中的边界：v4 实际为 read-only；v5 虽在临时 frozen spec 标注 workspace-write，child command 仍为 read-only，因此不能作为沙箱因果对照；v6 的 child command 实际为 workspace-write，目标 Skill 精确读取仍被宿主策略拒绝。

当前 preflight 三项 raw SHA-256 也与文档一致：

- `frozen.json`：`8c27c103c1d89d000d57d088d369e944d9959061f95c8b67fc6e16f8694b50d0`
- `run-meta.json`：`e0fd8fa841478b601cb838df1130cdf84a4df35fe14ed9ee8bb611890d3c4f48`
- `native-results.json`：`ee7cca9e48ddfae526c56cee9ed1d0621775d86185fd566adca8c19718eb5e61`

按当前 analyzer 独立分类，baseline 为 2 次尝试、0 次路由选择、0 次正文加载、0 次策略阻断、2 次传输有效、2 次 operational success；probe 为 2 次尝试、2 次精确路由选择、0 次正文加载、2 次策略阻断、0 次传输有效、0 次 operational success。两个 probe 各有两条 agent message，并同时发生 output-last 绑定失败；这些失败保留为可分析数据，没有因 runner 的基础 valid 标志而丢弃。

把正式 analyzer 指向这份只执行 1/3 重复的 preflight 时，独立观察到 `ValueError: run does not contain every frozen repetition`，且目标输出文件未创建。preflight 因而不能通过正式门禁，也不能与正式结果合并。

## 门禁与授权边界

门禁对 baseline 路由误判、令牌泄漏、备用输出缺失、策略阻断和传输失败，以及 probe 路由缺失、正文加载缺失、策略阻断和传输失败分别执行零容忍检查。任一检查失败都会令 `business_comparison_authorized=false` 并打开基础设施调查；结果对象始终写死 `skill_change_authorized=false`。protocol 也明确规定 gate fail 时停止，不授权修改任何业务 Skill 或 catalog。

## 验证与限制

- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：154 项通过，1 项因当前 Windows 环境缺少创建符号链接权限而跳过。
- Round 27 定向测试：13/13 通过。
- `git diff --check`：通过。

本复核验证的是冻结设计、分类边界、raw 一致性与执行完整性，不是模型回答质量评测。preflight 只有 1/3 重复，且已显示宿主策略阻断，因此它只能预示正式门禁可能失败；是否失败仍须由不重试、不筛选的完整 12 条正式运行决定。ignored raw 的 SHA-256 可检测当前本地字节变化，但不是外部签名或时间戳证明。
