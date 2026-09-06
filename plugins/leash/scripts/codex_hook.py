"""Thin Codex hook adapter: translate Codex JSON to core observations/responses."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.engine import DEPENDENCIES, Observation, evaluate, load, log, normalize, save
PATCH_PATH = re.compile(r"^(?:\+\+\+\s+(?:b/)?|\*\*\*\s+(?:Update|Add|Delete) File:\s+)(.+)$", re.M)
COMMAND_PATH = re.compile(r"(?<![\w.-])((?:[\w.-]+/)+[\w.-]+|(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|Dockerfile|\.env[\w.-]*))(?![\w.-])")
LEASH_COMMAND = re.compile(r"^\$?leash\s+(scope|off)\b", re.I)
def project(event): return Path(event.get("cwd") or ".").resolve()
def paths_for(event):
    command = str((event.get("tool_input") or {}).get("command", ""))
    if event.get("tool_name") == "apply_patch": return tuple(normalize(path) for path in PATCH_PATH.findall(command) if path != "/dev/null")
    return tuple(dict.fromkeys(normalize(path) for path in COMMAND_PATH.findall(command)))
def control(event, state):
    prompt = event.get("prompt", "").strip()
    if DEPENDENCIES.search(prompt): state["dependencies_allowed"] = True
    match = LEASH_COMMAND.match(prompt)
    if not match: return None
    action, words = match.group(1).lower(), prompt.split()
    if action == "scope" and len(words) > 2:
        state.update(enabled=True, scope=words[2:])
        message = f"Leash: scope set to {', '.join(words[2:])}. Out-of-scope changes will be blocked."
    elif action == "off":
        state["enabled"] = False
        message = "Leash: disabled for this project and session."
    else: message = "Leash: use leash scope <glob...> or leash off."
    return {"decision": "block", "reason": message}
def main():
    event = json.load(sys.stdin); root, session = project(event), event.get("session_id", "default"); state = load(root, session)
    if event.get("hook_event_name") == "UserPromptSubmit":
        response = control(event, state); save(root, session, state)
        if response: print(json.dumps(response))
        return
    observed = Observation(event.get("tool_name", ""), paths_for(event), str((event.get("tool_input") or {}).get("command", "")), session, state.get("dependencies_allowed", False)); decision = evaluate(observed, state)
    if decision.action == "allow": state["touched"] = sorted(set(state.get("touched", [])) | set(observed.paths))
    else: state["flags"] = state.get("flags", 0) + 1; log(root, observed, decision)
    save(root, session, state)
    if decision.action == "block": print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": f"Leash: {decision.reason}."}}))
if __name__ == "__main__": main()
