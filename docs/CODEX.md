# Codex installation

ds-harness runs under Codex as well as Claude Code, from the same checkout and the same adapter:

```bash
bin/install.sh --host codex --adapter /path/to/<your-adapter>
```

The Codex binding (`hosts/codex/install.py`, contract in `hosts/codex/host.json`) links the core skills and the adapter's `extensions.skills` into `~/.agents/skills`, writes `~/.ds-harness/adapter` (the same pointer every host uses; `~/.codex/ds-harness-adapter` is still written for 0.2 compatibility), renders a Codex custom agent (`~/.codex/agents/<name>.toml`) from every core and adapter agent, registers the PreToolUse guard in `~/.codex/hooks.json`, and appends any MCP server the adapter declares in `platform.tools` (spec 0.3) to `~/.codex/config.toml`. An existing non-symlink skill directory is moved to `~/.agents/skill-backups/` first. If the adapter sets `extensions.entry_skill`, a one-page router skill is written under that name.

Both hosts resolve the **same** adapter directory, so there is one set of rules, one findings file and one approvals directory (`operations.governance.approvals_dir`, by default `~/.claude/approvals`; the guard's BLOCKED message prints the exact path to touch).

A spec 0.2 adapter names its tools only; configure them in `~/.codex/config.toml` the way the adapter's `platform.setup` describes. A spec 0.3 adapter declares command, args and env, and the binding registers them. Restart Codex after installation and trust the changed hook definition when Codex asks.

Not yet verified: that Codex invokes PreToolUse hooks with the same stdin JSON (`tool_input.command` / `tool_input.query_file`) the guard parses. Test with a read-only query that contains one of the adapter's `sampling_patterns`; it must be blocked.
