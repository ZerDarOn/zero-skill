# Round 25 静态冻结预检

日期：2026-09-13

本轮先对最终候选字节运行 `prepare_skill_comparison.py`，未调用模型。受 Git 忽略的本地预检目录为 `evaluations/runs/conversation-explicit-boundary-preflight-20260913-v1`。

静态预检得到 4 个唯一 case、2 个机制且每组恰好 2 题。每题只有 1 个用户回合和 4 项硬标准。配置固定 2 臂、每题每臂 3 次，因此正式运行应产生 24 条轨迹、24 个生成回合、12 个匿名盲评项目和 96 个标准布尔值。prepare 生成 8 个 arm-case 测试定义；所有 `vars` 只有 `prompt`，硬标准仅位于 metadata，没有完整标准进入模型 prompt。

baseline fixture 为空。ours fixture 只包含 `conversation-rehearsal` 的 `SKILL.md` 与 `references/example.md`，技能包 SHA-256 为 `b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`，与当前 0.1.1 一致。

冻结绑定：

- comparison spec SHA-256：`856a665b510188e0b3fac0b0139934c3b027610d59bd765170e38c33ba39d98f`
- cases SHA-256：`3cdbd35e433adc04af7e89621f859dac5a3fb733e5c1a5a3a54f4723c682d78d`
- prepared frozen evidence SHA-256：`6380be21384552cbbca1dae7095b918fb9bc653c1e806fbfd9ca184b0fdcfa44`
- prepared config SHA-256：`a00e231245b63d4939e30d7d6bb5eda20fcfedf1a740929c8c384bc238fcf351`
- prepared tests SHA-256：`b31597a950711ab66701cd279a3daa6f6a091e13fc40de2260861fd83158844f`

这只证明冻结来源、prepare 产物、两臂 fixture、prompt 隔离和计划规模相互一致。它没有产生质量分、偏好或候选门槛结果，也不能证明正式 24 条轨迹会技术有效。
