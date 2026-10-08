"""Adapter resolution shared by every ds-harness script.

An *adapter* is a directory that teaches the harness about one data platform and one
team: fetch limits, SQL dialect checks, file naming, forbidden words, vocabulary,
guard patterns, reference docs. The core never hard-codes any of that.

Resolution order (first hit wins):
  1. $DS_HARNESS_ADAPTER_DIR        absolute path to an adapter directory
  2. $DS_HARNESS_ADAPTER            adapter name under <plugin root>/adapters/
  3. <plugin root>/adapters/_template   (checks degrade to "please fill in your adapter")

<plugin root> is $CLAUDE_PLUGIN_ROOT when installed as a plugin, otherwise the
repository root inferred from this file's location.
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]  # skills/_shared/harness_config.py -> repo


def plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return Path(env) if env else REPO_ROOT


def adapter_dir() -> Path:
    d = os.environ.get("DS_HARNESS_ADAPTER_DIR")
    if d:
        return Path(d).expanduser()
    name = os.environ.get("DS_HARNESS_ADAPTER", "_template")
    return plugin_root() / "adapters" / name


def load() -> dict:
    d = adapter_dir()
    cfg_path = d / "adapter.json"
    if not cfg_path.exists():
        raise SystemExit(f"adapter.json not found at {cfg_path}. Set DS_HARNESS_ADAPTER or DS_HARNESS_ADAPTER_DIR, "
                         f"or copy adapters/_template to adapters/<your-team> and fill it in.")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["_dir"] = str(d)
    cfg["_is_template"] = d.name == "_template"
    return cfg


def path(cfg: dict, rel: str) -> Path:
    return Path(cfg["_dir"]) / rel


def compile_all(patterns, flags=re.I):
    return [re.compile(p, flags) for p in (patterns or [])]


def load_checks_module(cfg: dict):
    """Optional adapter-provided python module with `sql_checks(sql_text, region) -> (errors, warnings)`."""
    rel = (cfg.get("sql") or {}).get("dialect_checks")
    if not rel:
        return None
    p = path(cfg, rel)
    if not p.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("adapter_checks", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod
