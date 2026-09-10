# 工程补丁三方对照

比较无技能、debug-evidence-triage 0.1.1，以及 Superpowers 固定提交的 systematic-debugging、test-driven-development、verification-before-completion 和相关引用。两个合成 Python 异步项目，每组每题两次，共12个修复实验，每个最多三轮模型回答。

## 执行边界

本机CLI原生工具预检返回 blocked by policy，未获得命令输出，因此没有继续尝试绕过模型工具限制。本轮使用明确的文本补丁协议：模型只提交JSON，实施代理先读取候选源代码与测试，再批准评测运行器在新的合成副本中应用并执行。运行器的本地执行是用户授权的评测操作，不宣称模型自主使用工具。

这测量的是给定完整小项目、复现日志和有限反馈下的补丁产物，不能外推真实仓库导航、权限交互、线上部署或生产数据排障。我们的技能以证据排查为主，此处由用户明确授权修复，测量其在修复任务上的迁移表现。

## 材料与验收

- [冻结协议](protocol.json)：任务、分组、模型、回合预算及判定标准。
- `fixtures/*/public/`：交给模型的README、原始模块与公开复现。
- `fixtures/*/heldout/`：不交给模型的额外验收与参考实现。
- [当前夹具复验](fixture-verification-current.json)由[复验脚本](verify_fixtures.py)绑定规范化后的源码：原始代码失败、参考实现通过；[历史准备记录](fixture-verification.json)另保留故意不完整修复通过公开测试却不能通过额外验收的证据。
- [运行器](run_comparison.py)：生成、审阅批准、应用与测试、最终验收分开执行。空测试、跳过测试和仅退出码为0不足以通过验收。

额外验收要求都来自公开README，不引入模型不知道的功能。主要指标是不可修改的公开测试与额外验收全部通过、原文件受保护，以及模型新增的回归测试在最终实现通过、在原始实现能因相关缺陷失败。仅导入不存在的私有符号而失败不能证明回归价值。

所有公开测试反馈进入下一轮；额外验收和对原始实现的回归挑战只在最后运行，不反馈给模型。中间失败允许在既定三轮内改正，全部保留，不是静默重试。各组共享初始失败日志，因此只测从已复现问题出发的修复，不测自主寻找复现的能力。

## 运行与记录

使用现有Codex登录，固定gpt-5.6-sol / medium。初始化先冻结协议、完整技能包和项目文件，再创建12个独立副本。模型调用仍为只读临时会话、显式技能加载、禁止直接工具；每轮最多两个调用并发，完整对话只在本实验内重放。

只有用户授权模型评测时才运行：

```sh
python evaluations/comparisons/engineering-three-arm-01/run_comparison.py init
python evaluations/comparisons/engineering-three-arm-01/run_comparison.py generate --root <run-directory> --step 1
```

生成后实施代理必须读取完整候选代码，确认其仅处理合成任务、没有越界操作，再写 `reviewed-step-1.json`，将实验编号映射到对应输出SHA-256。然后才能运行 `apply`。后续回合按同一流程推进，最后执行 `acceptance`。不要为了跑通直接自动批准未经阅读的代码。

测试使用独立Python进程及 `-B`，避免快速替换模块后误用字节码缓存；源文件按字节复制。反馈中的临时项目与用户目录路径替换为占位符，其他错误内容不改，原始测试输出另存临时副本的 `.evaluation-logs/`。原始模型响应与模型事件保存于被忽略的 `evaluations/runs/`。

[上游来源](../../fixtures/upstreams/superpowers/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/provenance.json)附MIT许可证和原始版权声明。全部上游文件未修改，引用脚本作为文本资料保留，没有运行或安装。writing-good-tests中针对编写技能才提到的writing-skills不属于这两项Python修复的依赖。

结果只用于探索，不改技能版本、原94项活动用例或experimental状态。实施代理编题和审阅，不是独立人工评测；最多三轮和JSON协议也会改变各技能的自然工作方式。
