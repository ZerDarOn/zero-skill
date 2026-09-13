# Round 28 独立工程复核

日期：2026-09-13

## 初次发现

独立审查先发现三类问题：矛盾的成功 stdout 与失败 stderr 会误放行；doctor 白名单字段值可能携带本机路径；版本探针超时或启动失败会在停止证据写出前中断。第一次修订后又发现分类详情和版本字符串未经过最终脱敏层。

实现随后改为失败 stderr 优先，所有公开字符串值统一路径脱敏，版本探针异常降级为结构化字段并继续执行 canary。每个缺口均增加了构造型负向回归，诊断重新运行到 v3；早期 v1、v2 只留在 ignored 本机目录，不作为公开结论来源。

## 最终结论

最终复核未发现 P0–P3 问题，可以提交：

- provisioning 或 policy stderr 优先于退出码和令牌，矛盾结果 fail closed；
- `classification.error_detail`、`codex_version`、版本探针错误以及 doctor 允许字段的字符串值均做路径脱敏；
- 版本探针超时、启动错误、非零退出或空输出不会绕过 canary 或证据保全；
- 包装器失败路径在调用原生 runner 前停止，保存的轨迹数、回合数和模型调用数均为 0；
- ignored v3 三项证据与机器报告一致，evidence projection 可复算；
- 历史 `run_native_resume.py` 保持冻结哈希 `cac3e238d717f7a268d9b6800bec11002eaa5d3e54ddf2458f65a2983e9912b5`。

## 验证

- Round 28 与相邻历史证据定向测试：19 项通过；
- 全套单元测试：177 项通过，1 项因 Windows 符号链接权限跳过；
- `python scripts/validate_collection.py`：通过；
- `git diff --check`：通过。

复核任务只读检查，没有修改工作区文件。
