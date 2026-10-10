# Project-wide Agent Rules

## Primary rule

This is a learning-first production-minded AI engineering project.

Do not generate large amounts of code without first explaining the design and the reason for the change.

## Mandatory behavior

- Work incrementally.
- Verify every meaningful implementation.
- Do not fabricate metrics.
- Do not fabricate project achievements.
- Do not add technology without a real reason.
- Prefer simple architecture.
- Keep ML/NLP/agent/API concerns modular.
- Explain new ML, NLP, Python and FastAPI concepts before using them.
- Never hide errors; diagnose root causes.
- Keep the implementation interview-defensible.
- Keep security practices conservative and defensive.
- Do not commit secrets.

## Learning requirement

The developer must understand every core component well enough to explain:

1. what it does
2. why it exists
3. how data flows through it
4. why the chosen implementation was used
5. what its limitations are

## Implementation requirement

Before a major change:

- explain the change
- list expected files
- state verification steps

After a major change:

- run tests/checks
- summarize files changed
- explain important decisions
- record real results
- identify the next phase

## Learning Documentation

Maintain `docs/learning/` throughout the project.

Whenever a meaningful concept is taught, doubt is resolved, debugging lesson is discovered, or important technical decision is made, update the relevant learning notes proactively.

The notes must reflect the actual project and should be understandable independently of the conversation.

## Git Protocol — TWO REMOTES (MANDATORY)

This project uses two GitHub remotes. Every commit must be pushed to BOTH.

### Remote map

| Remote name | URL | What it contains |
|---|---|---|
| `origin` | https://github.com/Shubh6665/ai-phising-risk-platform.git | Project source code only |
| `learning` | https://github.com/Shubh6665/ai-phising-project.git | Everything: code + docs/learning + .agents + AGENTS.md + implementation_plan.md |

### Push rule — always do both

After every commit:

```bash
git push origin main    # platform repo — code only (gitignore blocks non-code)
git push learning main  # full learning repo — everything
```

Or as a one-liner:

```bash
git push origin main && git push learning main
```

### What each repo contains

**`origin` (platform repo) — code only:**
- `src/`
- `tests/`
- `pyproject.toml`
- `notebooks/`
- `scripts/`
- `data/`
- `model_artifacts/`
- `README.md`
- `.env.example`
- `.gitignore`

**`learning` (full repo) — everything above PLUS:**
- `docs/learning/`
- `.agents/`
- `AGENTS.md`
- `implementation_plan.md`

The `.gitignore` on the platform repo permanently blocks `docs/learning/`, `.agents/`, `AGENTS.md`, `implementation_plan.md` from being committed there.

### NEVER do

- `git push` (without specifying the remote) — it only pushes to `origin`, missing `learning`
- Skip `git push learning main` after a commit — the learning repo falls behind
- Commit `docs/learning/` changes and forget to push them to `learning`

### Verify remotes are configured

```bash
git remote -v
# Should show both origin and learning
```

If `learning` is missing (e.g. fresh clone):

```bash
git remote add learning https://github.com/Shubh6665/ai-phising-project.git
```