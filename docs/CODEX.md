# Codex installation

ds-harness runs under Codex as well as Claude Code, from the same checkout and the same adapter:

```bash
bin/install-codex.sh /path/to/<your-adapter>
```

The installer links the core skills and the adapter's `extensions.skills` into `~/.agents/skills`, writes `~/.codex/ds-harness-adapter` (one line: the adapter path, the same path the Claude Code installer writes to `~/.claude/ds-harness-adapter`), generates a Codex custom agent (`~/.codex/agents/<name>.toml`) from every core and adapter agent, and registers the PreToolUse guard in `~/.codex/hooks.json`. An existing non-symlink skill directory is moved to `~/.agents/skill-backups/` first. If the adapter sets `extensions.entry_skill`, a one-page router skill is written under that name.

Both hosts resolve the **same** adapter directory, so there is one set of rules, one findings file and one approvals directory (`operations.governance.approvals_dir`, by default `~/.claude/approvals`; the guard's BLOCKED message prints the exact path to touch).

Platform tooling (query CLI or MCP server) is configured in `~/.codex/config.toml` the way the adapter's `platform.setup` describes; the core does not know your tools. Restart Codex after installation and trust the changed hook definition when Codex asks.

Not yet verified: that Codex invokes PreToolUse hooks with the same stdin JSON (`tool_input.command` / `tool_input.query_file`) the guard parses. Test with a read-only query that contains one of the adapter's `sampling_patterns`; it must be blocked.
