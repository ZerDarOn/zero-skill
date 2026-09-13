# 第二十八轮质量打磨：Windows 原生沙箱运行前门禁

日期：2026-09-13

## 本轮结论

第二十七轮的隐式 Skill 正文加载失败已经定位到当前 Windows 宿主的沙箱 provisioning，而不是业务 Skill 内容。直接运行受限 `codex sandbox` canary 时，命令尚未启动便返回 `helper_unknown_error: apply deny-read ACLs`；`codex doctor --json` 独立报告 elevated Windows sandbox provisioning 失败，并给出修复或重装受认可 Codex 发行版的建议。

本轮没有模型调用、业务轨迹或评分，也没有修改 Skill、版本、catalog、evidence 和活动用例。十六个 Skill 仍为 `experimental`，活动用例仍为 148 项。

## 排除过程

`CODEX_HOME` 位于系统临时目录不是充分原因。第二十七轮 exploratory v6 已把工作区和隔离 HOME 移到仓库授权根内，且不再出现临时目录辅助程序警告，但 `Get-Location` 和精确 Skill 文件读取仍被阻止。

用户或项目命令规则也不能解释该轮子进程：记录的命令同时使用 `--ignore-user-config` 与 `--ignore-rules`。更小的直接 canary 不经过模型、不选择 Skill，也在命令启动前失败。两条证据共同支持当前宿主沙箱 provisioning 是阻断层。

`codex doctor` 另提示 Microsoft Defender 可能干扰 Codex，并称排除项未经验证。这只是修复线索；本轮没有证明 Defender 是根因，报告明确保存 `endpoint_protection_confirmed_as_root_cause: false`。

## 新门禁

新增 `preflight_host_sandbox.py`，用内置 `:read-only` 权限档案启动一条无网络、无写入的 PowerShell canary。只有退出码为 0 且 stdout 严格等于固定令牌才通过；provisioning 错误、策略阻断、近似输出、超时和启动错误分别分类。

新增 `run_native_resume_with_host_preflight.py` 包装器，并要求新规格显式声明 `native_resume.require_host_sandbox_preflight: true`。若 canary 失败，包装器先写出脱敏诊断与停止元数据，再于任何模型调用前退出；通过后才委托给原有 `run_native_resume.py`。共享 runner 保持原字节，第二十六、二十七轮冻结的基础设施哈希仍有效，历史协议也未被回写。

公开机器报告只保留沙箱字段白名单，并对允许字段、错误分类和版本信息中的字符串值再次做路径脱敏；另保存规范化命令、错误文本和原始字节哈希，不保存 doctor 输出中的用户路径、认证状态或其他主机信息。独立复核后修正了失败优先级、所有公开值的脱敏与版本探针容错，并用新的 v3 诊断重跑。ignored 本机记录显示 canary 用时 78ms、模型调用 0、重试 0。

## 下一步门槛

修复宿主后先重跑同一受限 canary。它通过之前，不重跑隐式 Skill 正文加载，也不启动业务隐式质量对照。canary 通过只解除命令启动阻断；仍需重新证明路由选择、正文加载、传输完整性和零策略阻断。

Codex 官方文档说明 Skill 正文按需加载，项目 Skill 从 `.agents/skills` 发现；沙箱文档说明只读与工作区写入模式限制命令和文件访问。本轮将宿主可执行性独立成前置条件，与这些分层保持一致：

- [Codex Skills](https://developers.openai.com/codex/skills/)
- [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing)
- [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

## 对应证据

- [诊断协议](../evaluations/comparisons/native-host-sandbox-preflight-21/protocol.json)
- [协议说明](../evaluations/comparisons/native-host-sandbox-preflight-21/README.md)
- [机器报告](../evaluations/reports/native-host-sandbox-preflight-round-28.json)
- [运行前门禁实现](../evaluations/native_resume/preflight_host_sandbox.py)
- [带门禁的原生会话包装器](../evaluations/native_resume/run_native_resume_with_host_preflight.py)
- [独立工程复核](../evaluations/comparisons/native-host-sandbox-preflight-21/final-review-independent.md)
