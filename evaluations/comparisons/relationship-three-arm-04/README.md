# Relationship review three-arm 04

这是一组运行前冻结的显式完整包三方 pilot：无技能、`relationship-review` 0.1.1、LoveHelper `relationship-copilot` 固定提交。六个全新合成恋爱沟通任务各运行一次，覆盖短回复、自然暧昧、混合信号、明确拒绝、标签化冲突和单向付出。

本轮特意同时测试两类价值：本地技能的证据与边界克制，以及 LoveHelper 更强的具体语气、推进动作和领域覆盖。评分不把“更进攻”自动视为更好，也不把“更谨慎”自动视为更好；以用户目标、现有证据、明确边界和可直接使用性为准。

## 上游范围

当前公开专门恋爱 Skill 的 Star 都很低。2026-09-11 刷新时，LoveHelper 为 3、`YuzeHao2023/love-skill` 为 15、`yubowen123/guanxi-skills` 为 25；最后一个仓库未声明许可证。LoveHelper 热度不高，但任务入口最贴近“看聊天、给下一句、下一步怎么做”，且固定提交有 MIT，因此选作领域对照。Star 只用于发现，不进入评分。

夹具保留固定提交 `1e391e26fd1c1bfee06e4daa9b439086a098a49b` 的原路径和原字节，包括顶层 MIT、署名说明、copilot 入口、默认 playbook 和阶段判定入口；[provenance.json](../../fixtures/upstreams/love-helper/1e391e26fd1c1bfee06e4daa9b439086a098a49b/provenance.json) 记录 URL、哈希、未包含内容和用途。没有安装或执行上游脚本。

LoveHelper 的明显长处是先给可发送内容、引用具体聊天、把建议落成策略动作，以及在有窗口时生成更有情境感的语气。风险是默认阶段分数、进攻性和“框架”语言可能超过用户需要；明确拒绝、证据不足和单向付出题会直接检验其安全边界。本地技能不照搬分数、人格口吻或操控术语。

## 执行

```powershell
python evaluations/comparisons/relationship-three-arm-04/run_comparison.py
```

运行器把技能文件完整内联给对应实验臂，避免当前宿主无法读取 `SKILL.md` 引用文件的问题。任务正文完全相同，硬标准不会进入生成提示；失败不重试。结果写入被忽略的 `evaluations/runs/relationship-three-arm-04-*`，先填写 `blind-review-form.json`，再用通用计分器揭盲：

```powershell
python evaluations/promptfoo/score_blind_review.py --run <运行目录> --review <已完成评分文件>
```

这不是隐式发现测试，也不是临床建议、真人关系结论或完整上游产品验收。初次评阅若由模型完成，必须写成模型辅助盲评，不能称为独立人工评审。
