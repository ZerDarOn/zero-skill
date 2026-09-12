# Conversation native-resume comparison

This frozen comparison tests `conversation-rehearsal` 0.1.1 against a no-skill baseline with real Codex session continuation. It uses six synthetic trajectories, two arms, and three repetitions. Eighteen anonymous review items compare 36 trajectories containing 84 generated turns. Five cases are forward checks; `simulation-not-real-person-evidence` is an explicit native-session paraphrase regression for an existing evidence boundary.

The first turn is prepared by the repository's standard native-skill freezer. Every later turn is sent only to the explicit thread ID returned by the first `codex exec`; the runner forbids `--last` and `--ephemeral`, keeps one isolated home and Git fixture per trajectory, and records output, JSONL events, usage, return status, thread ID, and hash chains. A failed session or evidence gate stays in the run and invalidates formal scoring.

Run from the repository root:

```powershell
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/conversation-native-resume-two-arm-17/promptfoo.json --output evaluations/runs/<new-run>
python evaluations/native_resume/run_native_resume.py --run evaluations/runs/<new-run>
python evaluations/native_resume/summarize_native_resume.py --run evaluations/runs/<new-run>
python evaluations/promptfoo/score_blind_review.py --run evaluations/runs/<new-run> --review evaluations/runs/<new-run>/completed-review.json
python evaluations/native_resume/analyze_native_review.py --run evaluations/runs/<new-run> --review evaluations/runs/<new-run>/completed-review.json --review-result evaluations/runs/<new-run>/review-result-completed-review.json
```

The blind packet shows the frozen user turns and each anonymous candidate's assistant turns in order. It does not contain arm IDs, package hashes, or the randomization salt. Review all four criteria before opening the key. Criterion 1 is the preregistered core boundary for each case.

The candidate-design gate opens only when both cases in one mechanism have at least two of three core failures for `ours`, while the matching baseline cases each have at most one of three. Preference and aggregate score are diagnostic and cannot override this gate.
