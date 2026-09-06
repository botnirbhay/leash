# Leash

Leash is a deterministic scope guardrail for Codex CLI. It measures file paths and commands at tool-call time; it does not judge code quality or use an LLM.

After you declare a scope, Leash blocks detected edits outside it. It is most useful in long-running Codex sessions, where the original task boundary can get lost among later requests.

## Install

```powershell
codex plugin marketplace add botnirbhay/leash
codex plugin add leash@leash-local
```

Start a new Codex session in the project you want to protect. Run `/hooks` once to review and trust Leash if Codex asks.

If hooks are disabled, add this to `~/.codex/config.toml`:

```toml
[features]
hooks = true
```

## Use

Type these in the Codex chat, not PowerShell:

```text
leash scope src/main/java/com/example/** src/test/java/com/example/**
```

Every detected write outside those paths is denied before it runs. To disable Leash for the current project and session:

```text
leash off
```

A leading `$` is also accepted for compatibility.

## What it blocks

- Edits outside a declared scope
- Lockfile edits unless the task mentions dependencies
- Dependency-install commands not mentioned in the task
- CI and high-risk config edits, including `.github/workflows/**`, `.env*`, and `Dockerfile`
- A sixth distinct touched file in one session

Blocked events are logged locally in `.leash/log.jsonl`; session state is stored in `.leash/config.json`.

## Update

```powershell
codex plugin marketplace upgrade leash-local
codex plugin add leash@leash-local
```

Start a new Codex session after updating.

## Local development

```powershell
codex plugin marketplace add C:\path\to\Leash
codex plugin add leash@leash-local
cd plugins\leash
py -3 -m unittest discover -s tests -v
```

## Project structure

```text
.agents/plugins/marketplace.json  Codex marketplace entry
plugins/leash/core/               Agent-agnostic policy engine
plugins/leash/scripts/            Codex hook adapter
plugins/leash/hooks/              Codex lifecycle registration
plugins/leash/tests/              Dependency-free tests
```

The core accepts generic observations—tool name, paths, and command—and returns `allow` or `block`. A future Claude Code or Cursor integration should be a new adapter, without changing the core.

## Status

This MVP supports Codex CLI only. It is installable from GitHub, but is not yet listed in OpenAI’s public Plugins Directory.
