# Round 24 native-resume preflight

Date: 2026-09-13

The final-spec preflight used `codex-cli 0.154.0-alpha.6.2`, `gpt-5.6-sol`, medium reasoning, and the selected two-turn case `stop-roleplay-one-real-message`. It ran one baseline trajectory and one explicit `conversation-rehearsal` trajectory. The ignored local run is `evaluations/runs/conversation-native-resume-preflight-20260913-v2`.

Both trajectories completed: 2/2 trajectories and 4/4 turns were technically valid. Each trajectory received a distinct explicit thread ID; its second turn resumed exactly that ID, returned the same ID, read only the current frozen user message from stdin, retained `sandbox_mode="read-only"`, and used neither `--last` nor `--ephemeral`. The baseline execution fixture was empty. The ours fixture and copied workspace matched the frozen two-file Skill package. Every final output matched the unique JSONL `agent_message`; event, stderr, output, prior-output chain, usage, and result hashes recomputed successfully.

Frozen bindings:

- comparison spec SHA-256: `396258ed8b3490227997674c3725a5d6fa94839101783250d77e3258a1f4b765`
- cases SHA-256: `e01512e42d6ba821b46538f50ef34aeb0d5a0eab2fd821afff4c75718baa7642`
- prepared frozen evidence SHA-256: `60e3df653226d902343669eb5af4d01285f8862777a1b9a9ef2dc9c4d7db3252`
- native results SHA-256: `0d9821e79eb2793f247f122ac41a77e318bba11a98a308f420721e53ceaa961d`
- `conversation-rehearsal` package SHA-256: `b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`

This is an infrastructure preflight, not a scored quality result. It uses one selected case and one repetition, and it does not count toward the formal 18-item blind review or candidate gate. The earlier `v1` local run proved the same basic path but is obsolete because the common prompt changed afterward; only `v2` binds the final comparison spec above.
