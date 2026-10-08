"""Adapter resolution and access, shared by every ds-harness script and hook helper.

An adapter is a directory with adapter.json (spec 0.2, see adapter-spec/) and eight sub-directories, one per
extension point. The core never hard-codes platform, team or language specifics; it reads them from here.

Resolution order:
  1. $DS_HARNESS_ADAPTER_DIR          absolute path (preferred for private adapters)
  2. $DS_HARNESS_ADAPTER              name under <harness>/adapters/
  3. <harness>/adapters/_template     checks degrade to "fill in your adapter"

<harness> is $CLAUDE_PLUGIN_ROOT when installed as a plugin, otherwise the repository root inferred from this file.
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
REQUIRED = ["platform", "delivery", "operations"]


def harness_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return Path(env) if env else REPO_ROOT


POINTER = Path.home() / ".claude" / "ds-harness-adapter"  # written by bin/install.sh; one line, the adapter path


def adapter_dir() -> Path:
    d = os.environ.get("DS_HARNESS_ADAPTER_DIR")
    if d:
        return Path(d).expanduser()
    if os.environ.get("DS_HARNESS_ADAPTER"):
        return harness_root() / "adapters" / os.environ["DS_HARNESS_ADAPTER"]
    if POINTER.exists():
        p = POINTER.read_text(encoding="utf-8").strip()
        if p:
            return Path(p).expanduser()
    return harness_root() / "adapters" / "_template"


def load() -> dict:
    d = adapter_dir()
    cfg_path = d / "adapter.json"
    if not cfg_path.exists():
        raise SystemExit(f"adapter.json not found at {cfg_path}. Set DS_HARNESS_ADAPTER_DIR (or DS_HARNESS_ADAPTER), "
                         f"or copy adapters/_template to your own adapter and fill it in (adapter-spec/README.md).")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if cfg.get("spec_version") != "0.2":
        raise SystemExit(f"{cfg_path}: spec_version must be \"0.2\" (got {cfg.get('spec_version')!r}); see adapter-spec/README.md")
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise SystemExit(f"{cfg_path}: missing required extension points {missing}")
    cfg["_dir"] = str(d)
    cfg["_is_template"] = d.name == "_template"
    return cfg


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
    return f"adapter={cfg['name']} ({cfg['_dir']})"
