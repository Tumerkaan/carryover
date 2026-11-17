# Mapping table: Claude Code ⇄ Codex

**Source column:**
- `L`: checked against real files on a local install (Claude Code 2.1.318, Codex Desktop 0.167.0-alpha, Windows, 2026-11-17).
- `O`: taken from OpenAI's own `migrate-to-codex` skill (`references/differences.md`, docs last checked 2026-04-20, Apache-2.0). That reference covers Claude → Codex in much more depth; read it when you go in that direction.
- `U`: not verified. Run the adapter's discovery step before relying on it.

Status words match the final report: `Carried`, `Check before using`, `Not carried`.

## Instructions and memory

| Concept | Claude Code | Codex | Claude → Codex | Codex → Claude | Src |
| --- | --- | --- | --- | --- | --- |
| Project instructions | `CLAUDE.md` (also `.claude/CLAUDE.md`, `CLAUDE.local.md`) | `AGENTS.md` (hierarchical, per directory) | Carried; rewrite tool-specific text | Carried; Claude Code reads `CLAUDE.md`, so either write `CLAUDE.md` containing `@AGENTS.md` or merge into it | L/O |
| User instructions | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | Carried (ask user) | Carried (ask user) | L |
| Auto memory | `~/.claude/projects/<encoded-path>/memory/` (`MEMORY.md` index + one file per fact) | `~/.codex/memories/` (`memory_summary.md`, `MEMORY.md`, `rollout_summaries/*.md`); global, not per project | Distill into bundle; Codex builds its own memories from new sessions | Distill project-relevant entries into bundle; optionally seed Claude memory files | L |
| Session history | `~/.claude/projects/<encoded-path>/*.jsonl`; deleted after `cleanupPeriodDays` (default 30) | newer builds: `~/.codex/state_<n>.sqlite` + `thread_history_<n>.sqlite`; older: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | Distill (`/import` copies raw chats for the last ~30 days, U) | Distill; no official importer. Raw transcript converters exist (cx2cc, cc-sync, transession) but are out of scope | L |

## MCP

| Concept | Claude Code | Codex | Claude → Codex | Codex → Claude | Src |
| --- | --- | --- | --- | --- | --- |
| Project servers | `.mcp.json` `mcpServers` | `.codex/config.toml` `[mcp_servers.<name>]` | Carried | Carried | L/O |
| User servers | `~/.claude.json` `mcpServers` (or `claude mcp add -s user`) | `~/.codex/config.toml` | Carried | Carried; prefer `claude mcp add` so the CLI writes the file | L/O |
| stdio | `command`, `args`, `env` | `command`, `args`, `env`, `env_vars` (names forwarded from parent env) | Carried | Carried; `env_vars = ["X"]` → `"env": {"X": "${X}"}` | L/O |
| HTTP | `type: "http"`, `url`, `headers` | `url`, `bearer_token_env_var`, `http_headers`, `env_http_headers` | Carried / Check | Carried; `bearer_token_env_var = "T"` → `headers.Authorization: "Bearer ${T}"` | O |
| SSE | `type: "sse"` | not supported | Not carried | n/a | O |
| Tool filters | none per server (use permissions `mcp__server__tool`) | `enabled_tools`, `disabled_tools` | n/a | Check: allowlist → `permissions.allow` for listed tools + `deny` for the server's other tools (needs the real tool list; see SKILL step 5) | O/U |
| Timeouts, `cwd` | not per server | `startup_timeout_sec`, `tool_timeout_sec`, `cwd` | n/a | Not carried (note it) | O/U |

## Permissions and sandbox

| Concept | Claude Code | Codex | Claude → Codex | Codex → Claude | Src |
| --- | --- | --- | --- | --- | --- |
| Shell allow/deny/ask | `settings.json` `permissions.allow/ask/deny`, e.g. `Bash(git push:*)` | `~/.codex/rules/*.rules`, `prefix_rule(pattern=[...], decision="allow"\|"prompt"\|"forbidden")` | Check (no automatic converter, U) | Carried: `allow`→`allow`, `prompt`→`ask`, `forbidden`→`deny`; pattern list joined into `Bash(<words>:*)` | L (allow) / U (prompt, forbidden) |
| File read/edit rules | `Read(...)`, `Edit(...)` rules | no path-level rule; sandbox writable roots | Not carried (note) | n/a | L |
| Approval mode | `permissions.defaultMode` (`default`, `acceptEdits`, `plan`, `bypassPermissions`, ...) | `approval_policy` (`untrusted`, `on-request`, `never`, ...) | Check | Check: `untrusted`/`on-request`→`default`; `never` + `workspace-write`→`acceptEdits` (do not map to `bypassPermissions` without asking) | L/U |
| Sandbox | `sandbox.enabled` + settings | `sandbox_mode` (`read-only`, `workspace-write`, `danger-full-access`), `writable_roots`, network | Check | Check: report the old mode; Claude Code's sandbox is opt-in | L/U |
| Extra dirs | `permissions.additionalDirectories` | `writable_roots` | Check | Carried | L |
| Local-only overrides | `.claude/settings.local.json` | none | Not carried | n/a | O |

## Hooks

| Concept | Claude Code | Codex | Claude → Codex | Codex → Claude | Src |
| --- | --- | --- | --- | --- | --- |
| Where | `hooks` in `settings.json` | `.codex/hooks.json` + `[features].codex_hooks = true` | Check | Carried | O |
| PreToolUse / PostToolUse | all tools, matcher by tool name | shell commands only | Check | Carried; matcher becomes `Bash` | O |
| UserPromptSubmit, SessionStart, Stop | yes | yes (fewer matchers) | Check | Carried | O |
| Notification, PreCompact, SubagentStop, SessionEnd, ... | yes | no | Not carried | n/a | O |
| `notify` (turn complete) | `Stop` / `Notification` hook | `notify = [...]` in config | n/a | Carried as `Stop` hook only if the program is the user's own script; if it is part of the Codex app (a path under the Codex install, e.g. its computer-use helper), Not carried | O/U |
| Automations, goals (scheduled or self-continuing agent loops) | scheduled tasks / `/loop` (not a settings file) | Codex app automations and goals | Not carried | Not carried: list each with its schedule and prompt, so the user can recreate it by hand | U |
| Hook types | `command`, `prompt`, `agent`, `http` | `command` only | prompt/agent/http: Not carried | Carried | O |

## Agents, commands, skills, plugins

| Concept | Claude Code | Codex | Claude → Codex | Codex → Claude | Src |
| --- | --- | --- | --- | --- | --- |
| Subagents | `.claude/agents/*.md` (frontmatter `name`, `description`, `tools`, `model`, `effort`) | `.codex/agents/*.toml` (`developer_instructions`, `model`, `model_reasoning_effort`, `sandbox_mode`) | Check: tools become prompt text | Check: `developer_instructions` → body; `sandbox_mode = "read-only"` → `tools: Read, Grep, Glob`; model names do not carry | L/O |
| Custom commands | `.claude/commands/*.md` (`$ARGUMENTS`) | legacy `~/.codex/prompts/*.md`; now skills | Carried as skill | Carried as `.claude/commands/<name>.md` or skill | O/U |
| Skills | `.claude/skills/<name>/SKILL.md`, `~/.claude/skills/` | `.agents/skills/<name>/SKILL.md`; user skills seen under `~/.codex/skills/` | Carried | Carried; copy folder. Drop/flag Codex-only `agents/openai.yaml` | L/O |
| Plugins | `.claude/plugins/`, marketplaces | `[plugins."name@marketplace"]` in config | Not carried (manual) | Not carried (list them; user reinstalls the Claude equivalent if one exists) | L/O |
| Model choice | `model` in settings / agents | `model`, `model_reasoning_effort` | Not carried | Not carried (different model families) | O |

## Model vs tool

Switching the **model** inside the same tool (for example GLM or Kimi through Claude Code's Anthropic-compatible endpoint) moves nothing: files stay where they are. Only the instruction style may need tuning. carryover is for switching the **tool** (harness).
