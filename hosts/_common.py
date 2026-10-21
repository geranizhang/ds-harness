#!/usr/bin/env python3
"""Shared helpers for host bindings (hosts/<host>/*.py). Each host script is run as
    python3 hosts/<host>/<script>.py <adapter_dir>
and imports this file by path. Nothing team-specific lives here; everything comes from adapter.json."""
import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
sys.path.insert(0, str(CORE / "skills" / "_shared"))
import harness_config as hc  # noqa: E402

POINTER_DIR = Path.home() / ".ds-harness"


def expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def load_host(name: str) -> dict:
    return json.loads((HERE / name / "host.json").read_text(encoding="utf-8"))


def load_adapter(adapter_dir: str) -> dict:
    os.environ["DS_HARNESS_ADAPTER_DIR"] = str(Path(adapter_dir).resolve())
    return hc.load()


def manifest_path(host: str) -> Path:
    return POINTER_DIR / f"installed.{host}"


def record(host: str, path: Path):
    POINTER_DIR.mkdir(parents=True, exist_ok=True)
    with open(manifest_path(host), "a", encoding="utf-8") as f:
        f.write(str(path) + "\n")


def link(host: str, src: Path, dst: Path, backups: Path = None):
    """Symlink dst -> src. An existing real file/dir is moved to backups (if given) or left alone."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        if backups is None:
            print(f"  skip (exists, not a symlink): {dst}")
            return
        backups.mkdir(parents=True, exist_ok=True)
        moved = backups / f"{dst.name}-{os.getpid()}"
        dst.rename(moved)
        print(f"  moved existing {dst} -> {moved}")
    dst.symlink_to(src, target_is_directory=src.is_dir())
    record(host, dst)
    print(f"  {dst} -> {src}")


def core_skills():
    return [CORE / "skills" / s for s in ("analysis-brief", "analysis-workflow", "report-writing", "_shared")]


def adapter_skills(cfg: dict):
    d = hc.get(cfg, "extensions.skills")
    base = hc.path(cfg, d) if d else None
    return sorted(p for p in base.glob("*/") if (p / "SKILL.md").exists()) if base and base.is_dir() else []


def core_agents():
    return sorted((CORE / "agents").glob("*.md"))


def adapter_agents(cfg: dict):
    d = hc.get(cfg, "extensions.agents")
    base = hc.path(cfg, d) if d else None
    return sorted(base.glob("*.md")) if base and base.is_dir() else []


def parse_agent(path: Path):
    """Core agent format: YAML-ish front matter (name, description, tools, model) + markdown body."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"name": path.stem, "description": ""}, text
    fields = {}
    for line in parts[1].splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("'\"")   # front matter values may be quoted
    return fields, parts[2]


def tools(cfg: dict):
    return hc.tools(cfg)


def resolve_exec(decl: dict):
    return hc.resolve_exec(decl)


def mcp_invocation(decl: dict):
    """(command, args, env) for registering an mcp-kind declaration with a host, or None when it does not resolve."""
    ex = resolve_exec(decl)
    if not ex:
        return None
    return ex[0], ex[1:] + list(decl.get("mcp_args") or []), hc.tool_env(decl)


def write_pointer(host: str, adapter_dir: Path, profile: Path = None):
    POINTER_DIR.mkdir(parents=True, exist_ok=True)
    (POINTER_DIR / "adapter").write_text(str(adapter_dir) + "\n", encoding="utf-8")
    (POINTER_DIR / "host").write_text(host + "\n", encoding="utf-8")          # last installed host
    hosts_f = POINTER_DIR / "hosts"                                            # every host installed on this machine
    hosts = [h for h in hosts_f.read_text(encoding="utf-8").split() if h] if hosts_f.exists() else []
    if host not in hosts:
        hosts.append(host)
    hosts_f.write_text("\n".join(hosts) + "\n", encoding="utf-8")
    (POINTER_DIR / "harness").write_text(str(CORE) + "\n", encoding="utf-8")
    if profile:
        (POINTER_DIR / "profile").write_text(str(profile) + "\n", encoding="utf-8")
    print(f"  {POINTER_DIR}/adapter -> {adapter_dir}")
