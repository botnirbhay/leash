# Leash
Leash is a deterministic scope-creep guardrail for Codex CLI: **measure scope, don't judge code quality**. It does no LLM inference and has no dependencies.

## Structure
- `core/engine.py` — agent-agnostic matching, policy evaluation, session state, and JSONL audit logging.
- `scripts/codex_hook.py` — the thin Codex adapter; it only converts hook payloads to core observations and core decisions to hook responses.
- `hooks/hooks.json` — registers `UserPromptSubmit` controls and `PreToolUse` checks.

Future Claude Code or Cursor support means adding another adapter; do not change `core/`.

## Use
Run this in a Codex session:

```text
leash scope src/auth/**
```

Leash immediately blocks writes outside those globs. Run `leash off` to disable it for the current project and session. It also blocks lockfile edits and dependency installs unless dependencies were mentioned in the task, high-risk CI/config files, and a sixth distinct touched file. Every blocked event goes to `.leash/log.jsonl`; state is `.leash/config.json`.

## Install
```powershell
codex plugin marketplace add C:\Users\nhanjura\personalproj\Leash
codex plugin add leash@leash-local
```

Enable hooks in `~/.codex/config.toml` if needed:
```toml
[features]
hooks = true
```

Run core tests without Codex:
```powershell
py -3 -m unittest discover -s tests -v
```

