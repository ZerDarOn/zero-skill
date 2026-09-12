# 显式 Skill 调用可靠性

这是第 26 轮冻结候选。第 25 轮正式 v1 的 24 条 `conversation-rehearsal` 轨迹中，有一条先输出 Skill 加载进度，再尝试读取项目 Skill 文件并被策略阻止，最终产生两条 agent message。完整 v2 没有复现，但单次重跑不能证明风险消失。

本轮只衡量运行可靠性，不做回答质量盲评，也不据此修改业务 Skill。两个独立队列都使用 `gpt-5.6-sol`、medium、项目级显式调用、只读沙箱和每题 10 次重复：

- `canary`：无 Skill baseline 与合成 `explicit-invocation-probe`。两道题分别要求返回仅存在于探针 `SKILL.md` 中的不同令牌，用来证明正文确实被加载；baseline 返回令牌视为泄漏。
- `business`：无 Skill baseline 与 `conversation-rehearsal` 0.1.1。两道题复用第 25 轮的一道真人边界题和发生过无效轨迹的纯虚构题，只检查单一最终消息、事件绑定、无策略阻断和完整回合，不重新评分内容质量。

每个队列有 2 题 × 2 臂 × 10 次，共 40 条单轮轨迹；合计 80 条。两个队列都使用冻结种子随机化任务提交顺序，结果文件仍按 case、arm、repetition 排序，运行元数据保存实际提交顺序及其哈希。

门禁为零容忍：baseline 技术失败、探针 Skill 调用失败、baseline 令牌泄漏和业务 Skill 技术失败都必须为 0。任何失败只打开基础设施调查；它不授权修改 `conversation-rehearsal`、版本、catalog 状态或 evidence。即使 80/80 通过，也只能说明本次主机、模型、配置和样本下未复现，不能证明长期失败率为零。

正式运行前应完成静态检查、一次重复的独立预检和独立冻结前复核。预检使用单独目录，不进入正式统计；正式运行必须从冻结提交准备全新目录，不挑选或拼接轨迹。
