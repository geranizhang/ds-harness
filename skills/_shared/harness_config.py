"""Adapter resolution and access, shared by every ds-harness script and hook helper.

An adapter is a directory with adapter.json (spec 0.2, see adapter-spec/) and eight sub-directories, one per
extension point. The core never hard-codes platform, team or language specifics; it reads them from here.

Resolution order:
  1. $DS_HARNESS_ADAPTER_DIR          absolute path (preferred for private adapters)
  2. $DS_HARNESS_ADAPTER              name under <harness>/adapters/
  3. ~/.ds-harness/adapter            written by bin/install.sh for whichever host; one line, the adapter path
  4. ~/.claude/ds-harness-adapter, ~/.codex/ds-harness-adapter   0.2 per-host pointers, kept for compatibility
  5. <harness>/adapters/_template     checks degrade to "fill in your adapter"

<harness> is $CLAUDE_PLUGIN_ROOT when installed as a plugin, otherwise the repository root inferred from this file.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
REQUIRED = ["platform", "delivery", "operations"]
SPEC_VERSIONS = ("0.2", "0.3")

# Profile (spec 0.3): per-person overlay, ~/.ds-harness/profile.json (or the path in ~/.ds-harness/profile).
# Only these keys may be overridden; anything else is a team rule and load() refuses it.
PROFILE_KEYS = {
    "_comment": None,
    "workspace": "operations.workspace",                   # whole subtree, deep-merged
    "governance": {"approvals_dir": "operations.governance.approvals_dir"},
    "secrets": None,                                       # {ENV_NAME: value}; names must be in channel.secrets_env when declared
    "tools": None,                                         # {tool_name: {command|args|candidates|env|health_check}}
}
TOOL_OVERRIDE_KEYS = {"command", "args", "candidates", "env", "health_check"}


def harness_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return Path(env) if env else REPO_ROOT


POINTER_DIR = Path.home() / ".ds-harness"       # adapter / host / profile, one line each (bin/install.sh)
POINTERS = [                                     # 0.3 pointer first, then the 0.2 per-host pointers
    POINTER_DIR / "adapter",
    Path.home() / ".claude" / "ds-harness-adapter",
    Path.home() / ".codex" / "ds-harness-adapter",
]


def adapter_dir() -> Path:
    d = os.environ.get("DS_HARNESS_ADAPTER_DIR")
    if d:
        return Path(d).expanduser()
    if os.environ.get("DS_HARNESS_ADAPTER"):
        return harness_root() / "adapters" / os.environ["DS_HARNESS_ADAPTER"]
    for pointer in POINTERS:
        if pointer.exists():
            p = pointer.read_text(encoding="utf-8").strip()
            if p:
                return Path(p).expanduser()
    return harness_root() / "adapters" / "_template"


def profile_path() -> Path | None:
    """~/.ds-harness/profile (a path), else ~/.ds-harness/profile.json if it exists, else None. $DS_HARNESS_PROFILE overrides."""
    env = os.environ.get("DS_HARNESS_PROFILE")
    if env:
        return Path(env).expanduser()
    ptr = POINTER_DIR / "profile"
    if ptr.exists():
        p = ptr.read_text(encoding="utf-8").strip()
        if p:
            return Path(p).expanduser()
    default = POINTER_DIR / "profile.json"
    return default if default.exists() else None


def _deep_merge(dst: dict, src: dict):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v


def apply_profile(cfg: dict, prof: dict, source: str = "profile"):
    """Overlay a profile onto a loaded adapter config. Refuses keys outside PROFILE_KEYS (a team rule is not per-person)."""
    bad = [k for k in prof if k not in PROFILE_KEYS]
    if bad:
        raise SystemExit(f"{source}: keys not allowed in a profile: {bad}. Allowed: workspace, governance.approvals_dir, secrets, tools. "
                         f"Anything else is a team rule and belongs in the adapter (with a CHANGELOG line).")
    if "workspace" in prof:
        _deep_merge(cfg.setdefault("operations", {}).setdefault("workspace", {}), prof["workspace"])
    gov = prof.get("governance") or {}
    badg = [k for k in gov if k not in PROFILE_KEYS["governance"]]
    if badg:
        raise SystemExit(f"{source}: governance keys not allowed in a profile: {badg} (only approvals_dir)")
    if "approvals_dir" in gov:
        cfg.setdefault("operations", {}).setdefault("governance", {})["approvals_dir"] = gov["approvals_dir"]
    secrets = prof.get("secrets") or {}
    declared = get(cfg, "channel.secrets_env") or []
    bads = [k for k in secrets if declared and k not in declared]
    if bads:
        raise SystemExit(f"{source}: secrets not declared in channel.secrets_env: {bads}")
    cfg["_secrets"] = dict(secrets)
    for k, v in secrets.items():
        os.environ.setdefault(k, str(v))
    tool_over = prof.get("tools") or {}
    decls = {t["name"]: t for t in tools(cfg)}
    for name, over in tool_over.items():
        if name not in decls:
            raise SystemExit(f"{source}: tools.{name} is not declared in the adapter's platform.tools")
        badk = [k for k in over if k not in TOOL_OVERRIDE_KEYS]
        if badk:
            raise SystemExit(f"{source}: tools.{name} keys not allowed: {badk} (only {sorted(TOOL_OVERRIDE_KEYS)})")
        if "command" in over or "args" in over:
            decls[name]["candidates"] = [[over.get("command") or decls[name].get("command") or name] + list(over.get("args") or [])]
        for k in ("candidates", "env", "health_check"):
            if k in over:
                decls[name][k] = over[k]
    cfg["_profile"] = source
    return cfg


def load(profile: bool = True) -> dict:
    d = adapter_dir()
    cfg_path = d / "adapter.json"
    if not cfg_path.exists():
        raise SystemExit(f"adapter.json not found at {cfg_path}. Set DS_HARNESS_ADAPTER_DIR (or DS_HARNESS_ADAPTER), "
                         f"or copy adapters/_template to your own adapter and fill it in (adapter-spec/README.md).")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if cfg.get("spec_version") not in SPEC_VERSIONS:
        raise SystemExit(f"{cfg_path}: spec_version must be one of {SPEC_VERSIONS} (got {cfg.get('spec_version')!r}); see adapter-spec/README.md")
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise SystemExit(f"{cfg_path}: missing required extension points {missing}")
    cfg["_dir"] = str(d)
    cfg["_is_template"] = d.name == "_template"
    cfg["_profile"] = None
    cfg["_secrets"] = {}
    if isinstance(get(cfg, "platform.tools"), list):
        cfg["platform"]["tools"] = [dict(t) for t in cfg["platform"]["tools"]]   # own copies: profile may edit them
    if profile:
        pp = profile_path()
        if pp and pp.exists():
            apply_profile(cfg, json.loads(pp.read_text(encoding="utf-8")), str(pp))
    return cfg


# ---- tools (spec 0.3 declarations; the 0.2 {query_cli, mcp_server} pair is normalized) ----

def tools(cfg: dict) -> list:
    t = get(cfg, "platform.tools")
    if isinstance(t, list):
        return t
    out = []
    if isinstance(t, dict):
        if t.get("query_cli"):
            out.append({"name": t["query_cli"], "kind": "cli", "legacy": True})
        if t.get("mcp_server") and t["mcp_server"] != t.get("query_cli"):
            out.append({"name": t["mcp_server"], "kind": "mcp", "legacy": True})
        elif t.get("mcp_server") and out:
            out[0]["kind"] = "mcp"
    return out


def tool_decl(cfg: dict, name: str) -> dict | None:
    return next((t for t in tools(cfg) if t.get("name") == name), None)


def _expand(s: str) -> str:
    return os.path.expandvars(os.path.expanduser(s))


def resolve_exec(decl: dict):
    """The first candidate invocation (list of argv parts) whose program exists and whose path-like parts resolve.
    Globs in parts resolve to the newest match. Returns None when nothing resolves."""
    cands = decl.get("candidates")
    if not cands:
        if decl.get("command"):
            cands = [[decl["command"]] + list(decl.get("args") or [])]
        elif decl.get("legacy"):
            cands = [[decl["name"]]]
        else:
            return None
    for cand in cands:
        parts, ok = [], True
        for i, raw in enumerate(cand):
            part = _expand(raw)
            if any(ch in part for ch in "*?["):
                hits = sorted(glob.glob(part), key=os.path.getmtime)
                if not hits:
                    ok = False
                    break
                part = hits[-1]
            if i == 0:
                if not ((os.path.isabs(part) and os.path.exists(part)) or shutil.which(part)):
                    ok = False
                    break
                part = part if os.path.isabs(part) else (shutil.which(part) or part)
            elif ("/" in part) and not os.path.exists(part):
                ok = False
                break
            parts.append(part)
        if ok:
            return parts
    return None


def tool_exec(name: str, cfg: dict = None) -> list:
    """argv prefix for a declared tool (e.g. ['/opt/homebrew/bin/your-cli'] or ['node', '/path/cli.js']); SystemExit if unresolved."""
    cfg = cfg or load()
    decl = tool_decl(cfg, name)
    if decl is None:
        raise SystemExit(f"tool '{name}' is not declared in the adapter's platform.tools")
    ex = resolve_exec(decl)
    if not ex:
        hint = decl.get("setup_doc") or "the adapter's platform.setup"
        raise SystemExit(f"tool '{name}' not found on this machine (candidates: {decl.get('candidates') or decl.get('command') or name}); see {hint}")
    return ex


def tool_env(decl: dict) -> dict:
    return {k: _expand(str(v)) for k, v in (decl.get("env") or {}).items()}


def secret(name: str, cfg: dict = None):
    """A declared secret: env var first (the profile exports its secrets there on load), else None."""
    v = os.environ.get(name)
    if v:
        return v
    cfg = cfg or load()
    return (cfg.get("_secrets") or {}).get(name)


def get(cfg: dict, dotted: str, default=None):
    """cfg lookup by dotted path: get(cfg, 'delivery.doc.colloquial_words', [])."""
    cur = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if cur is not None else default


def path(cfg: dict, rel: str) -> Path:
    return Path(cfg["_dir"]) / rel


def compile_all(patterns, flags=re.I):
    return [re.compile(p, flags) for p in (patterns or [])]


def load_module(cfg: dict, dotted: str):
    """Load an adapter-provided python file named at cfg[dotted] (e.g. platform.sql.dialect_checks, evals.cases)."""
    rel = get(cfg, dotted)
    if not rel:
        return None
    p = path(cfg, rel)
    if not p.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("adapter_" + dotted.replace(".", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def describe(cfg: dict) -> str:
    """One line for script banners."""
    prof = f", profile={cfg['_profile']}" if cfg.get("_profile") else ""
    return f"adapter={cfg['name']} ({cfg['_dir']}{prof})"
