#!/usr/bin/env python3
"""Claude Code binding: link skills and agents into ~/.claude, register the guard hook, register declared MCP tools."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402

HOST = "claude-code"


def main(adapter_dir):
    host = c.load_host(HOST)
    cfg = c.load_adapter(adapter_dir)
    adapter = Path(cfg["_dir"])
    skills, agents = c.expand(host["skills_dir"]), c.expand(host["agents_dir"])
    c.manifest_path(HOST).unlink(missing_ok=True)
    print("skills:")
    for s in c.core_skills() + c.adapter_skills(cfg):
        c.link(HOST, s, skills / s.name)
    print("agents (core format is the host format here: symlinked):")
    for a in c.core_agents() + c.adapter_agents(cfg):
        c.link(HOST, a, agents / a.name)
    print("hook:")
    c.link(HOST, c.CORE / "hooks" / "guard.sh", c.expand(host["hooks"]["guard_link"]))
    register_hook(host)
    print("tools:")
    register_tools(cfg, host)
    print("pointers:")
    c.write_pointer(HOST, adapter)
    legacy = c.expand(host["legacy_pointer"])
    legacy.write_text(str(adapter) + "\n", encoding="utf-8")
    print(f"  {legacy} -> {adapter} (0.2 compatibility)")


def register_hook(host):
    p = c.expand(host["hooks"]["file"])
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    pre = d.setdefault("hooks", {}).setdefault(host["hooks"]["event"], [])
    entry = {"matcher": "Bash|mcp__.*__run_command", "hooks": [{"type": "command", "command": f"bash {host['hooks']['guard_link']}"}]}
    if any("ds-harness-guard" in json.dumps(e) for e in pre):
        print(f"  {p}: PreToolUse entry present")
        return
    pre.append(entry)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {p}: PreToolUse entry added")


def register_tools(cfg, host):
    decls = c.tools(cfg)
    if not decls:
        print("  none declared (platform.tools)")
        return
    p = c.expand(host["tools"]["file"])
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    servers = d.setdefault("mcpServers", {})
    changed = False
    for t in decls:
        if t.get("kind") != "mcp":
            continue
        if t.get("legacy"):
            print(f"  {t['name']}: declared by name only (spec 0.2); register it by hand per platform.setup, or declare command/args in platform.tools (spec 0.3)")
            continue
        if t["name"] in servers:
            print(f"  {t['name']}: already in {p} (left as is)")
            continue
        cmd = c.resolve_command(t)
        entry = {"type": "stdio", "command": cmd, "args": t.get("args") or []}
        if t.get("env"):
            entry["env"] = t["env"]
        servers[t["name"]] = entry
        changed = True
        print(f"  {t['name']}: added to {p} ({cmd} {' '.join(entry['args'])})")
    if changed:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
