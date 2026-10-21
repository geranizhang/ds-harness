#!/usr/bin/env python3
"""Codex binding: link skills into ~/.agents/skills, render every agent to ~/.codex/agents/<name>.toml,
register the guard in ~/.codex/hooks.json, register declared MCP servers in ~/.codex/config.toml,
write the optional entry skill (adapter.json → extensions.entry_skill)."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402

HOST = "codex"


def main(adapter_dir):
    host = c.load_host(HOST)
    cfg = c.load_adapter(adapter_dir)
    adapter = Path(cfg["_dir"])
    skills, agents = c.expand(host["skills_dir"]), c.expand(host["agents_dir"])
    backups = c.expand(host["skill_backups"])
    c.manifest_path(HOST).unlink(missing_ok=True)
    print("skills:")
    for s in c.core_skills() + c.adapter_skills(cfg):
        c.link(HOST, s, skills / s.name, backups)
    print("agents (rendered to toml):")
    agents.mkdir(parents=True, exist_ok=True)
    for a in c.core_agents() + c.adapter_agents(cfg):
        render_agent(a, agents)
    print("hook:")
    register_hook(host)
    print("tools:")
    register_tools(cfg, host)
    entry_skill(cfg, skills)
    print("pointers:")
    c.write_pointer(HOST, adapter)
    legacy = c.expand(host["legacy_pointer"])
    legacy.write_text(str(adapter) + "\n", encoding="utf-8")
    print(f"  {legacy} -> {adapter} (0.2 compatibility)")
    print("\nRestart Codex to reload skills and agents; review and trust the updated hook when Codex asks.")


def render_agent(src: Path, target: Path):
    fields, body = c.parse_agent(src)
    body = body.replace("`<harness>` is the plugin root", f"`<harness>` is `{c.CORE}`").replace("`<harness>` is this repository's root", f"`<harness>` is `{c.CORE}`")
    dest = target / f"{fields.get('name', src.stem)}.toml"
    dest.write_text(f'name = {json.dumps(fields.get("name", src.stem), ensure_ascii=False)}\n'
                    f'description = {json.dumps(fields.get("description", ""), ensure_ascii=False)}\n'
                    f'developer_instructions = {json.dumps(body.strip(), ensure_ascii=False)}\n', encoding="utf-8")
    c.record(HOST, dest)
    print(f"  {dest}  <- {src}")


def register_hook(host):
    p = c.expand(host["hooks"]["file"])
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"hooks": {}}
    pre = d.setdefault("hooks", {}).setdefault(host["hooks"]["event"], [])
    pre[:] = [e for e in pre if "ds-harness" not in json.dumps(e)]
    pre.append({"matcher": "Bash|mcp__.*__run_command", "hooks": [{"type": "command", "command": f"bash '{c.CORE / 'hooks' / 'guard.sh'}'"}]})
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {p}: PreToolUse entry written (stdin protocol: {host['hooks']['stdin']})")


def register_tools(cfg, host):
    decls = c.tools(cfg)
    if not decls:
        print("  none declared (platform.tools)")
        return
    p = c.expand(host["tools"]["file"])
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    for t in decls:
        if t.get("kind") != "mcp":
            continue
        if t.get("legacy"):
            print(f"  {t['name']}: declared by name only (spec 0.2); register it by hand per platform.setup, or declare command/args in platform.tools (spec 0.3)")
            continue
        if re.search(rf"^\[mcp_servers\.{re.escape(t['name'])}\]", text, re.M):
            print(f"  {t['name']}: already in {p} (left as is)")
            continue
        inv = c.mcp_invocation(t)
        if not inv:
            print(f"  {t['name']}: not found on this machine (candidates: {t.get('candidates') or t.get('command')}); see {t.get('setup_doc') or 'platform.setup'}")
            continue
        cmd, args, env = inv
        block = [f"\n[mcp_servers.{t['name']}]", f'command = {json.dumps(cmd)}', f"args = {json.dumps(args)}", "startup_timeout_sec = 60"]
        if env:
            block.append(f"\n[mcp_servers.{t['name']}.env]")
            block += [f'{k} = {json.dumps(v)}' for k, v in env.items()]
        text = text.rstrip("\n") + "\n" + "\n".join(block) + "\n"
        print(f"  {t['name']}: appended to {p} ({cmd} {' '.join(args)})")
    p.write_text(text, encoding="utf-8")


def entry_skill(cfg, skills: Path):
    e = c.hc.get(cfg, "extensions.entry_skill")
    if not e or not e.get("name"):
        return
    d = skills / e["name"]
    d.mkdir(parents=True, exist_ok=True)
    body = e.get("body") or ("Use `analysis-workflow` as the end-to-end process, `analysis-brief` for unfamiliar or complex questions, "
                             "and `report-writing` for report structure. Team rules come from the active adapter (`~/.ds-harness/adapter`) through its `adapter.json`.")
    (d / "SKILL.md").write_text(f"---\nname: {e['name']}\ndescription: {e.get('description', '')}\n---\n\n{body}\n", encoding="utf-8")
    c.record(HOST, d / "SKILL.md")
    print(f"entry skill: {d / 'SKILL.md'}")


if __name__ == "__main__":
    main(sys.argv[1])
