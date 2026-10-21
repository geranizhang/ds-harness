# Architecture 0.3: core × host × adapter (+ profile)

Status: **design, not implemented.** Written 2026-10-20 after the Codex install exposed where the 0.2 split stops short. `DESIGN.md` records the 0.2 core/adapter boundary; this page proposes the next cut. Nothing here changes the analysis flow, the gates, the agents' jobs or the validators.

## 1. Goal

One sentence: **a team's whole way of working is a template that plugs into a fixed framework, and the agent host is a swappable part.**

- The **framework** (ds-harness core) is complete on its own: question → brief → retrieval → review → report → follow-up, four human gates, agent roles, validators, guard logic.
- A **team template** (the adapter) says which tables, definitions, rules, exemplars, tools and prior knowledge the framework runs on. One team writes it once; every member plugs the same template in and gets identical tool calls and identical knowledge.
- The **host** (Claude Code, Codex, a future runtime) is a binding layer: where skills go, what format agents take, how hooks and tools are registered. Changing host changes nothing in the framework or the template.
- A **profile** holds what differs per person: secrets, local paths, approval directory.

Today the first two exist. The third is two ad-hoc installers in `bin/`, and the fourth is mixed into the adapter. This document separates them.

## 2. The four layers and the test for each

| Layer | Answers | Lives in | Test: a thing belongs here iff … |
|---|---|---|---|
| core | how is analysis done well | `ds-harness/` (public) | it holds for any data team on any host |
| host | how does runtime X load skills, agents, hooks, tools | `ds-harness/hosts/<host>/` (public) | it changes when the runtime changes and for no other reason |
| adapter | what does this team analyze, with what, under which rules | the team's private repo | it is the same for every member of the team |
| profile | what is specific to this person and this machine | `~/.ds-harness/profile.json` (never in git) | two members of the same team would write different values |

The 0.2 test ("swap the platform names — is the rule still true?") remains the core/adapter test. Two new tests sit beside it: **swap the runtime** (host vs everything else) and **swap the person** (profile vs adapter).

Things that are in the wrong layer today:

| Item | Where it is | Where it belongs |
|---|---|---|
| `bin/install.sh` (Claude Code), `bin/install-codex.sh` (Codex) | core `bin/` | `hosts/claude-code/`, `hosts/codex/` |
| agent `.md` → Codex `.toml` conversion by regex | `install-codex.sh` | `hosts/codex/render_agent.py`, from a declared agent schema |
| hook registration (`settings.json` vs `hooks.json`) | each installer | each host directory |
| how to register the query MCP server (`platform/setup.md`, prose) | adapter, for humans | adapter **declares** the tool; the host **registers** it |
| `operations.workspace.projects_root`, `operations.governance.approvals_dir` | adapter | profile (adapter keeps the default) |
| `channel/secrets.json`, chat ids, agent ids | adapter (git-ignored file) | profile |
| absolute local paths in scripts (e.g. a CLI's npx cache path) | adapter skill scripts | resolved from the tool declaration at runtime |

## 3. Host binding

```
hosts/
  claude-code/
    host.json          what this host can do and where things go
    install.sh         link skills, render agents, register hook and tools, write pointer
    render_agent.py    agent.md (core format) → host format (here: identity, .md stays .md)
    register_tools.py  tool declarations → ~/.claude.json mcpServers (or `claude mcp add`)
    register_hook.py   PreToolUse entry → ~/.claude/settings.json
    verify.sh          pointer, links, hook present, each tool's health check
  codex/
    host.json
    install.sh
    render_agent.py    agent.md → ~/.codex/agents/<name>.toml
    register_tools.py  tool declarations → ~/.codex/config.toml [mcp_servers.*]
    register_hook.py   → ~/.codex/hooks.json
    verify.sh
```

`host.json` (contract, so a new host is a directory and nothing else changes):

```json
{
  "name": "codex",
  "skills_dir": "~/.agents/skills",
  "agents_dir": "~/.codex/agents",
  "agent_format": "toml",
  "hooks": {"file": "~/.codex/hooks.json", "event": "PreToolUse", "stdin": "claude-compatible | unknown"},
  "tools": {"file": "~/.codex/config.toml", "format": "toml-mcp-servers"},
  "capabilities": {"subagents": true, "hooks": true, "mcp": true}
}
```

The **core agent format** is what `agents/*.md` already is: YAML front matter (`name`, `description`, `tools`, optional `model`) + body. Hosts render from it; nobody edits a rendered file. A host that lacks a capability (no sub-agents, no hooks) says so in `host.json` and `verify.sh` reports what the workflow loses (e.g. "no hook: the sampling guard runs only as a validator, not as a block").

One pointer directory replaces the per-host pointers: `~/.ds-harness/` with `adapter` (path), `profile` (path), `host` (name). `harness_config.adapter_dir()` reads it first and keeps reading the 0.2 pointers (`~/.claude/ds-harness-adapter`, `~/.codex/ds-harness-adapter`) as fallbacks for one minor version.

## 4. Tool declarations in the adapter (spec 0.3)

`platform.tools` grows from two names into a list the host can act on:

```json
"tools": [
  {
    "name": "bytedcli",
    "kind": "mcp",
    "command": "bytedcli", "args": ["mcp"],
    "env": {"NPM_CONFIG_REGISTRY": "http://bnpm.byted.org"},
    "resolve": ["/opt/homebrew/bin/bytedcli", "~/.npm/_npx/*/node_modules/@bytedance-dev/bytedcli/dist/bytedcli.js"],
    "health_check": "bytedcli auth status",
    "mcp_tool_names": ["mcp__bytedcli__run_command", "mcp__bytedcli__list_commands"],
    "setup_doc": "platform/setup.md"
  },
  {"name": "lark-cli", "kind": "cli", "health_check": "lark-cli auth status", "setup_doc": "delivery/conventions.md"}
]
```

- `kind: mcp` → the host's `register_tools.py` writes the server entry in the host's own format. `kind: cli` → `verify.sh` checks it is on PATH and runs the health check.
- `resolve` is an ordered list of candidate executables (globs allowed); the first that exists is used. Adapter scripts that today hard-code a path call `harness_config.tool_path("bytedcli")` instead.
- Secrets never appear here; `env` values that are secrets are written as `$VAR_NAME` and come from the profile.
- The guard's `compliance.guard.command_patterns` and `mcp_tool` can be derived from `mcp_tool_names` + `name`; 0.3 keeps them explicit for compatibility and `verify.sh` warns when they disagree.
- `platform/setup.md` stays as the human runbook for login flows and failure signatures; it stops being the only place the server command is written.

`adapter.schema.json` gets the new shape; `spec_version` becomes `"0.3"`; a 0.2 adapter still loads (tools list optional, two-name object accepted and warned about).

## 5. Profile

`~/.ds-harness/profile.json`:

```json
{
  "workspace": {"projects_root": "~/work/projects"},
  "governance": {"approvals_dir": "~/.ds-harness/approvals"},
  "secrets": {"TT_TABLE_QUERY_CHAT_ID": "...", "TT_DATA_AGENT_ID": "...", "TT_DATA_AGENT_APP_ID": "..."},
  "tools": {"bytedcli": {"command": "/custom/path/bytedcli"}}
}
```

Rules:

- The profile may override **only an allow-listed set of keys**: `operations.workspace.*`, `operations.governance.approvals_dir`, `channel` secrets named in `channel.secrets_env`, and per-tool `command` / `args` / `env`. Everything else in the adapter is team rule and a profile cannot touch it; `harness_config.load()` refuses unknown keys so a rule cannot be changed by accident.
- `harness_config.load()` returns adapter ⊕ profile; scripts, hook and agents see one merged config and never read the profile themselves.
- The adapter keeps sensible defaults for every overridable key so a profile is optional; `install` creates an empty one.
- `channel/secrets.json` and `channel.secrets_env` become a compatibility path: if the profile has the key, it wins.

## 6. One entry point

```bash
bin/install.sh --host claude-code --adapter /path/to/adapter [--profile ~/.ds-harness/profile.json]
bin/install.sh --host codex       --adapter /path/to/adapter
bin/install.sh --uninstall [--host codex]
bin/doctor.sh                       # pointer, links, hook, tools (health checks), evals summary
```

`install.sh` reads `hosts/<host>/host.json`, calls that host's scripts in order (skills → agents → hook → tools → pointer), then runs `verify.sh`. The team repo's one-line `install.sh` wrapper stays, defaulting the adapter path and forwarding `--host`.

## 7. Knowledge sources (small, deliberate)

`knowledge.sources`: a list of `{title, url_or_path, kind: wiki|doc|dashboard, last_checked}` recording where `tables.md` / `metrics.md` / `domain.md` content came from. **No automatic sync.** Hand curation is why the handbooks are trustworthy; the list exists so a newcomer can go to the source and so `doctor` can flag entries not checked in N days.

## 8. What the colleague does after 0.3

```bash
git clone --recurse-submodules <team repo> tt-live-ds
cd tt-live-ds && ./install.sh --host claude-code      # or --host codex
#  → prompts for the three secrets (or reads ~/.ds-harness/profile.json), registers the query MCP server,
#    links skills, renders agents, registers the guard, runs doctor
```

Same template, same tools, same knowledge, on whichever host they use. No "照文档配 MCP" step.

## 9. Migration

| Step | Core | Adapter (tt-live-ds) | Machines |
|---|---|---|---|
| 1 | add `hosts/claude-code/` by moving `bin/install.sh` logic; `bin/install.sh` becomes the dispatcher | — | reinstall; pointers migrate to `~/.ds-harness/` |
| 2 | add `hosts/codex/` from `install-codex.sh`; delete the old script | — | reinstall on the Codex machine |
| 3 | spec 0.3: tools list + profile allow-list in `harness_config`; schema; `doctor.sh` | declare `bytedcli`, `lark-cli`; move the two hard-coded CLI paths in weekly-attribution scripts to `tool_path()` | create profile; secrets move out of `channel/secrets.json` |
| 4 | `knowledge.sources` in schema and template | fill it from the links already in `domain.md` / `tables.md` | — |
| 5 | evals: `run_validators` and `run_hook_tests` unchanged; add `hosts/<host>/verify.sh` to `doctor` | `evals_cases.py` unchanged | — |

Each step is independently shippable; 0.2 adapters keep working until step 3, and after it with warnings.

## 10. Decisions needed before building

1. **Single pointer directory `~/.ds-harness/`** (proposed) vs keeping one pointer per host. Single is simpler and makes "both hosts see the same adapter" structural rather than a convention.
2. **The profile allow-list.** Proposed: workspace paths, approvals dir, declared secrets, per-tool command/args/env. Anything else a person wants to change is a team rule change and goes through the adapter's CHANGELOG.
3. **Codex hook protocol.** `hosts/codex/host.json` marks `stdin: unknown` until a sampling query is shown to be blocked inside Codex. If Codex does not deliver the same JSON, `register_hook.py` needs a shim; worth verifying before step 2.
4. **Agents rendered for Codex: all of them** (core + adapter) is proposed; today only two are generated and the rest in `~/.codex/agents` are stale hand-made files.
5. **Wiki sync: no** (section 7). Confirm.

## 11. Non-goals

- Changing the analysis flow, the gates, the claim ladder or any validator.
- Supporting a host without sub-agents by rewriting the agents as prompts; such a host is declared as lacking the capability and the workflow runs in degraded mode.
- Making the adapter public or splitting it; it stays one private repo per team.
