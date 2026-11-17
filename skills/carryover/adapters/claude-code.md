# Adapter: Claude Code

Verified locally on Claude Code 2.1.318 (Windows), 2026-11-17. `~` = user home.

## Discovery (run first)

```
ls ~/.claude ~/.claude/projects
ls <project>/.claude <project>/CLAUDE.md <project>/.mcp.json
claude --version
claude mcp list            # resolved MCP servers for the current project
```

The project's data folder is `~/.claude/projects/<encoded>/`, where `<encoded>` is the absolute project path with every character that is not a letter or digit replaced by `-` (e.g. `C:\work\demo` → `C--work-demo`, `/home/a/demo` → `-home-a-demo`). If unsure, grep the `cwd` field in the `.jsonl` files instead.

## Where things live

| What | Project | User |
| --- | --- | --- |
| Instructions | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` (personal, gitignored) | `~/.claude/CLAUDE.md` |
| Settings (permissions, hooks, env) | `.claude/settings.json`, `.claude/settings.local.json` | `~/.claude/settings.json` |
| MCP | `.mcp.json` | `~/.claude.json` (`mcpServers`, also per-project entries) |
| Subagents | `.claude/agents/*.md` | `~/.claude/agents/*.md` |
| Commands | `.claude/commands/*.md` | `~/.claude/commands/*.md` |
| Skills | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` |
| Plugins | — | `~/.claude/plugins/` |
| Auto memory | — | `~/.claude/projects/<encoded>/memory/` (`MEMORY.md` index + files) |
| Transcripts | — | `~/.claude/projects/<encoded>/<session-uuid>.jsonl` |

**Retention:** transcripts older than `cleanupPeriodDays` (settings, default 30) are deleted. When leaving Claude Code, older history may already be gone; say so in the report.

## Transcript format (as read by `extract_history.py`)

One JSON object per line. Relevant fields: `type` (`user` / `assistant` / many others), `cwd`, `timestamp`, `sessionId`, `isSidechain`, `isMeta`, `isCompactSummary`, `message.content` (string, or list of blocks with `type` = `text` / `thinking` / `tool_use` / `tool_result` / `image`).
Kept: `text` blocks and string content of user/assistant records; compact summaries (marked). Dropped: thinking, tool calls and results, images, sidechain (subagent) and meta records, harness messages written into the user role (`<task-notification>`, `<local-command-...>`, `<bash-stdout>`), and injected tags such as `<system-reminder>` (with or without attributes) and `<command-name>`.

## Writing (when Claude Code is the destination)

- Instructions: if `AGENTS.md` exists and should stay the single source, write `CLAUDE.md` with one line `@AGENTS.md` plus Claude-specific notes. Otherwise merge into `CLAUDE.md`.
- MCP: prefer `claude mcp add <name> -s project -e KEY=value -- <command> <args...>` (writes `.mcp.json`); for HTTP `claude mcp add --transport http -s project <name> <url>` (flags checked with `claude mcp add --help` on 2.1.318). Env values stay as `${VAR}` references; never put a secret value in `-e`.
- Permissions: `.claude/settings.json` → `permissions.allow / ask / deny`, rule form `Bash(<prefix>:*)`.
- Hooks: `.claude/settings.json` → `hooks.<Event>[] = {matcher, hooks: [{type: "command", command}]}`.
- Subagents: `.claude/agents/<name>.md` with YAML frontmatter `name`, `description`, optional `tools`, `model`; body = system prompt.
- History: write the bundle; optionally add one memory file per key lesson to the auto-memory folder (only if the user wants Claude's memory seeded).

## Official importer

None from Codex as of 2026-11. Do everything in this skill.
