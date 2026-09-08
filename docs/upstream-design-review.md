# 上游设计取舍

调研日期：2026-09-08。下列是文档审阅所得的设计线索，不是项目效果背书。当前没有运行上游代码，也没有复制其实现或原始人物素材。候选详情见 `catalog/upstreams.json`。

| 项目与证据入口 | 可借鉴的设计 | 本集合的落实 | 需要调整的部分 |
| --- | --- | --- | --- |
| [女娲](https://github.com/alchaincyf/nuwa-skill/blob/main/SKILL.md) | 从多类材料提炼判断方式；保留不同来源与矛盾；说明视角局限 | P1 证据表、P3 观点来源；按缺口补材料 | 不照搬固定代理数、资料数、网站黑名单；资料重复出现不直接证明真实信念 |
| [Distilly](https://github.com/titanwings/distilly) | 版本化人物档案、显式纠正、局部使用或持久技能 | ADR-003；后续用例覆盖推翻旧结论 | 新版是开发预览；不为文件集合提前引入完整插件和存储系统 |
| [自己.skill](https://github.com/notdog1998/yourself-skill) | 个人记忆与行为表达分层、增量补充、修订回退 | 人物分析先支持自我复盘；纠正记录保留历史 | 人格标签可作用户描述，不能当成观察证据或固定身份 |
| [前任.skill](https://github.com/titanwings/ex-skill/blob/master/SKILL.md) | 关系记忆与表达模式分开，能处理对话纠正 | P4 分离记忆、人物设定与当轮虚构状态 | 角色像真人不等于准确还原；不接入自动聊天库提取 |
| [童锦程.skill](https://github.com/hotcoffeeshake/tong-jincheng-skill) | 明确观点出处、具体表达示例、说明素材覆盖范围 | P3 视角卡写适用情境和盲点，P2 提供可选表达 | 特定人物经验不能升级为普遍心理规律，绝对化恋爱判断需改为待检验解释 |
| [LoveHelper](https://github.com/Mowon0303/LoveHelper.skill/blob/main/relationship-copilot/SKILL.md) | 截图整理、阶段判断、回复建议可拆分协作 | P2 输入先核对发言人，再复盘与建议；素材不足时直接用文本 | 不把阶段分数包装成感情概率；截图识别只是可选入口 |
| [Crush-skill](https://github.com/T1anhu4/Crush-skill) | 演练与复盘、随互动变化的模拟状态 | P4 做可重试的对话练习，比较不同表达后果 | 数值是模拟参数；不能预测真人或将模拟回复回写为真人证据 |
| [Love Skill](https://github.com/pajama-studio/love-skill) | 同时考虑双方叙述，用情境选择沟通框架 | P2 保留双方目标、诉求和缺失材料 | 引用了心理学框架不代表项目自身已获效果验证；不预设诊断 |
| [相亲 skill](https://github.com/YuzeHao2023/love-skill) | 双方材料、差异和相处问题的结构化整理 | P2 讨论价值观与日常安排的具体问题 | 不输出未经校准的兼容性百分比；本地保存不代表模型处理不出网 |
| [人物 skill 合集](https://github.com/tmstack/awesome-persona-skills) | 按场景发现大量人物与主题项目 | 场景分类和候选登记 | 导航、完整技能、生成器分别登记，不能把清单当成已安装能力 |

## 转化为自己的实现

统一选择：材料 → 带来源的观察 → 可修订的解释 → 与任务相关的产出。

分析任务到解释为止；视角任务使用已注明来源的观点；模拟任务建立独立虚构状态。这个拆分让不同项目的长处可以配合，不需要叠加全部提示词。

代码级借鉴留到具体技能阶段：届时固定上游提交、审查依赖与授权、保留署名、执行合成用例。当前声明的许可证不是法律审查结论。
