# Adapter: Codex (CLI / Desktop)

Verified locally on Codex Desktop 0.167.0-alpha (Windows), 2026-11-17, unless marked `U` (unverified). `~` = user home; `CODEX_HOME` overrides `~/.codex`.

## Discovery (run first)

```
ls ~/.codex ~/.codex/sessions ~/.codex/memories ~/.codex/rules ~/.codex/skills
ls <project>/AGENTS.md <project>/.codex <project>/.agents
codex --version        # U: not on PATH for the Desktop install checked
codex mcp list         # U
```

Find this project's sessions by `session_meta.payload.cwd` (first line of each rollout file), not by file name. `~/.codex/session_index.jsonl` maps session id → thread name and update time.

## Where things live

| What | Project | User |
| --- | --- | --- |
| Instructions | `AGENTS.md` (any directory level), `AGENTS.override.md` (U) | `~/.codex/AGENTS.md` |
| Config (model, sandbox, approval, MCP, features, plugins) | `.codex/config.toml` | `~/.codex/config.toml`; per-project trust under `[projects.'<path>']` |
| MCP | `[mcp_servers.<name>]` in either config | same |
| Shell rules | — | `~/.codex/rules/*.rules` (`prefix_rule(pattern=[...], decision=...)`; only `decision="allow"` seen locally, `prompt` / `forbidden` are U) |
| Hooks | `.codex/hooks.json` + `[features].codex_hooks = true` (U, from OpenAI reference) | same under `~/.codex/` (U) |
| Subagents | `.codex/agents/*.toml` (U, from OpenAI reference) | `~/.codex/agents/` (U) |
| Prompts (legacy commands) | — | `~/.codex/prompts/*.md` (U) |
| Skills | `.agents/skills/<name>/SKILL.md` (from OpenAI reference) | `~/.codex/skills/<name>/SKILL.md` (L), `~/.agents/skills/` (U) |
| Plugins | — | `[plugins."<name>@<marketplace>"]` in config |
| Memories | — | `~/.codex/memories/` (`memory_summary.md`, `MEMORY.md`, `rollout_summaries/<date>-<slug>.md`), `[memories]` in config; global across projects |
| Transcripts (newer builds) | — | SQLite: `~/.codex/state_<n>.sqlite` (table `threads`: `id`, `cwd`, `title`, `source`, `created_at`, ...) + `~/.codex/thread_history_<n>.sqlite` (table `thread_items`) |
| Transcripts (older builds) | — | `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<id>.jsonl`, `~/.codex/archived_sessions/` |

**Important (L):** on the Desktop 0.167 install checked, almost every thread listed in `state_<n>.sqlite` had no rollout `.jsonl` left on disk; the messages lived only in the SQLite files. Read SQLite first; the extractor does this, then falls back to JSONL. Open the databases read-only (`?mode=ro`).

Never read `~/.codex/auth.json`.

## Transcript format: SQLite (as read by `extract_history.py`)

- `threads`: pick rows whose `cwd` is the project or a subfolder. Skip subagent and reviewer threads: `source` is a JSON string such as `{"subagent":...}`, or the id appears as `thread_spawn_edges.child_thread_id`.
- `thread_items` (`thread_id`, `rollout_ordinal`, `created_at_ms`, `item_type`, `item_json`):
  - `userMessage`: `content[]` items `{type: "text", text}`. The app wraps context around what the user typed: `<heartbeat>` automation pings (dropped), `# In app browser:` / `# Selected text:` / `# Files mentioned by the user:` followed by `## My request for Codex:` (only the text after that heading is kept), `<in-app-browser-context>` and similar tags (stripped).
  - `agentMessage`: `{text, phase}`, where `phase` is `commentary` (progress chatter, dropped) or `final_answer` (kept).
  - Everything else (`commandExecution`, `reasoning`, `fileChange`, `mcpToolCall`, `webSearch`, `contextCompaction` (no text), ...) is dropped.

## Transcript format: rollout JSONL

One JSON object per line: `{timestamp, type, payload}`.
- `type: session_meta` (first line): `payload.cwd`, `payload.cli_version`, `payload.originator`.
- `type: response_item`, `payload.type: message`, `payload.role` = `user` / `assistant` / `developer`; `payload.content[]` items of type `input_text` / `output_text` with `text`.
- Other records (`event_msg`, `turn_context`, `reasoning`, `custom_tool_call*`, `token_count`, ...) are dropped.
- Injected user messages that start with `# AGENTS.md instructions` / `## AGENTS.md instructions` or `<environment_context>` are dropped (they are not the user speaking).
- `type: compacted` with `payload.message` is kept as a summary (U: not observed locally).

## Writing (when Codex is the destination)

**First run the official path:** inside an interactive Codex session, `/import` (Claude Code → Codex; reported to carry instructions, MCP, skills, hooks, subagents, memories and recent chats, U), or OpenAI's `migrate-to-codex` skill for config. Then use this skill for what they leave out: distilled history (`decisions`, `lessons`, `tried-and-dropped`, `open-threads`), permission rules, and the explicit `Not carried` list.

- Instructions: `AGENTS.md`; link the bundle files from a `## Project history (carried over)` section.
- MCP: `codex mcp add <name> -- <command> <args...>` (U) or a `[mcp_servers.<name>]` table; env by name via `env_vars = ["VAR"]`.
- Shell rules: `~/.codex/rules/default.rules` lines `prefix_rule(pattern=["git", "push"], decision="prompt")`. This is a user-level file: **ASK** before writing.
