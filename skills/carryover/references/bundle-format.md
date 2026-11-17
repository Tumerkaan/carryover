# Bundle format (`<project>/carryover/`)

Tool-neutral. Any adapter reads from or writes to this. Plain Markdown so humans can review it and any agent can read it.

```
carryover/
  README.md              # source tool, destination tool, date, extractor version, scope chosen by user
  decisions.md
  lessons.md
  tried-and-dropped.md
  open-threads.md
  settings-inventory.md
  report.md              # final status table (same as the chat report)
```

## Entry format (decisions / lessons / tried-and-dropped / open-threads)

One `##` heading per entry, newest first.

```markdown
## Use Parquet instead of CSV for the cache
- When: 2026-04-12 (codex session)
- What: Cache layer writes Parquet via pyarrow.
- Why: CSV load took 40 s on the full set; Parquet 3 s. Types were also lost in CSV.
- Applies to: src/cache/
```

`tried-and-dropped.md` entries add `- Dropped because:` and, if known, `- Would reconsider if:`.

`open-threads.md` entries add `- Status:` (e.g. "failing test in tests/test_io.py", "half-written PR").

Rules:
- Every entry has a date and a source tool. No date in the history → write `When: unknown`.
- One fact per entry. If an entry needs more than ~6 lines, it is two entries.
- No secrets, no personal data that is not needed for the project.

## settings-inventory.md

One table. Values are tool-neutral; secrets by name only.

| Kind | Name | Scope | Source location | Neutral description | Value / shape |
| --- | --- | --- | --- | --- | --- |
| MCP | github | project | `.mcp.json` | stdio server | `npx -y @modelcontextprotocol/server-github`, env: `GITHUB_TOKEN` (name only) |
| Hook | format-on-stop | project | `.claude/settings.json` | run command when agent stops | `ruff format .` |
| Permission | allow git status | project | `.claude/settings.json` | allow shell prefix without asking | `git status` |
| Permission | deny rm -rf | user | `~/.codex/rules/default.rules` | forbid shell prefix | `rm -rf` |
| Sandbox | mode | project | `.codex/config.toml` | write inside workspace, ask for network | `workspace-write`, approval `on-request` |
| Subagent | reviewer | project | `.claude/agents/reviewer.md` | read-only reviewer | tools: Read, Grep; model: (dropped) |
| Command | /release | project | `.claude/commands/release.md` | prompt template with `$ARGUMENTS` | — |
| Skill | pdf-tools | user | `~/.claude/skills/pdf-tools/` | skill folder | — |

`Kind` is one of: `MCP`, `Hook`, `Permission`, `Sandbox`, `Subagent`, `Command`, `Skill`, `Plugin`, `Automation`, `Setting`, `Env`. Kinds, file names and status words stay in English; headings and field labels follow the bundle language.
