# Windows 原生沙箱运行前门禁

第二十七轮已经把隐式发现拆成路由选择、正文加载、策略阻断和传输完整性，但仍用 12 次模型调用才确认宿主不能启动读取命令。本诊断把模型与 Skill 全部移出变量，只要求 `codex sandbox` 在内置 `:read-only` 权限档案中启动一条无网络、无写入的 PowerShell canary。

通过条件是进程退出码为 0，并且 stdout 严格等于 `CODEX_WINDOWS_SANDBOX_CANARY_OK`。任何沙箱 provisioning 错误、策略阻断、超时、启动错误或近似输出都失败。失败只阻止依赖命令执行的后续评测，不改变 Skill 质量结论。

`preflight_host_sandbox.py` 保存脱敏命令、stdout/stderr、原始字节哈希和细分状态。新增的 `run_native_resume_with_host_preflight.py` 要求规格显式声明 `native_resume.require_host_sandbox_preflight: true`，先执行门禁，再委托给原生会话 runner；历史 runner 保持原字节，既有冻结证据不会失效。门禁失败时，包装器在任何模型调用前写出 `host-sandbox-preflight.json` 与 `host-preflight-stop.json`，随后以错误退出。

2026-09-13 的本机诊断没有通过：直接 canary 返回 `helper_unknown_error: apply deny-read ACLs`，`codex doctor --json` 同时报告 elevated Windows sandbox provisioning 失败。该结果支持把第二十七轮阻断定位到当前宿主沙箱，不支持修改业务 Skill，也没有证明 Microsoft Defender 是根因。
