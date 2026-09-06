"""Agent-agnostic, deterministic scope decisions."""
from __future__ import annotations
import fnmatch, json, re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "Cargo.lock", "poetry.lock", "Pipfile.lock", "composer.lock", "Gemfile.lock", "go.sum"}
CONFIG_PATTERNS = (".github/workflows/**", ".env*", "Dockerfile", "docker-compose*.yml", "docker-compose*.yaml", ".gitlab-ci.yml", ".circleci/**", "azure-pipelines*.yml", "Jenkinsfile")
INSTALL = re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|add)\b|\bpip(?:3)?\s+install\b|\bcargo\s+add\b|\b(?:gem|composer)\s+(?:install|require)\b", re.I)
DEPENDENCIES = re.compile(r"\b(?:dependenc(?:y|ies)|install|package(?:s)?|library|libraries|npm|pip|cargo)\b", re.I)
@dataclass(frozen=True)
class Observation: tool: str; paths: tuple[str, ...] = (); command: str = ""; session_id: str = "default"; dependencies_allowed: bool = False
@dataclass(frozen=True)
class Decision: action: str; rule: str = ""; reason: str = ""
def normalize(path):
    path = path.replace("\\", "/")
    while path.startswith("./"): path = path[2:]
    return path
def matches(path, pattern):
    path, pattern = normalize(path), normalize(pattern)
    return fnmatch.fnmatchcase(path, pattern) or (pattern.endswith("/**") and fnmatch.fnmatchcase(path, pattern[:-3]))
def is_config(path): return any(matches(path, pattern) for pattern in CONFIG_PATTERNS)
def evaluate(observation, state):
    if not state.get("enabled", True): return Decision("allow")
    flagged = lambda rule, reason: Decision("block", rule, reason)
    if observation.command and INSTALL.search(observation.command) and not observation.dependencies_allowed: return flagged("dependency-install", "dependency install is not part of the stated task")
    for path in map(normalize, observation.paths):
        if Path(path).name in LOCKFILES and not observation.dependencies_allowed: return flagged("lockfile", f"this edits lockfile {path}")
        if is_config(path): return flagged("high-risk-config", f"this edits high-risk config {path}")
        scope = state.get("scope", [])
        if scope and not any(matches(path, pattern) for pattern in scope): return flagged("outside-scope", f"this edits {path}, outside declared scope")
    prior, added = set(state.get("touched", [])), {normalize(path) for path in observation.paths}
    if len(prior | added) > state.get("file_limit", 5): return flagged("file-threshold", f"this session touches more than {state.get('file_limit', 5)} files")
    return Decision("allow")
def load(project, session_id):
    file = project / ".leash" / "config.json"
    try: document = json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError: document = {"sessions": {}}
    return document.setdefault("sessions", {}).setdefault(session_id, {"enabled": True, "scope": [], "touched": [], "flags": 0, "file_limit": 5, "dependencies_allowed": False})
def save(project, session_id, state):
    directory = project / ".leash"; directory.mkdir(parents=True, exist_ok=True); file = directory / "config.json"
    try: document = json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError: document = {"sessions": {}}
    document.setdefault("sessions", {})[session_id] = state
    file.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
def log(project, observation, decision):
    if decision.action == "allow": return
    directory = project / ".leash"; directory.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "tool": observation.tool, "paths": list(observation.paths), "command": observation.command, **asdict(decision)}
    with (directory / "log.jsonl").open("a", encoding="utf-8") as output: output.write(json.dumps(record) + "\n")
