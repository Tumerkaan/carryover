# Settings inventory

| Kind | Name | Scope | Source location | Neutral description | Value / shape |
| --- | --- | --- | --- | --- | --- |
| MCP | tiles-db | project | `.codex/config.toml` | stdio server | `uvx mcp-server-sqlite --db-path data/tiles.db`, env: `TILES_DB_KEY` (name only) |
| MCP | tiles-db tool filter | project | `.codex/config.toml` | only some tools enabled | `read_query`, `list_tables` |
| MCP | tiles-db startup timeout | project | `.codex/config.toml` | startup timeout | 20 s |
| MCP | docs | user | `~/.codex/config.toml` | HTTP server with bearer token | `https://mcp.example.com/docs`, token env: `DOCS_MCP_TOKEN` |
| Permission | git status | user | `~/.codex/rules/default.rules` | allow shell prefix | `git status` |
| Permission | pytest | user | `~/.codex/rules/default.rules` | allow shell prefix | `pytest` |
| Permission | git push | user | `~/.codex/rules/default.rules` | ask before shell prefix | `git push` |
| Permission | rm -rf | user | `~/.codex/rules/default.rules` | forbid shell prefix | `rm -rf` |
| Sandbox | mode | user | `~/.codex/config.toml` | write in workspace, ask on escalation | `workspace-write`, approval `on-request` |
| Hook | notify | user | `~/.codex/config.toml` | run command when a turn completes | `powershell -File C:/tools/notify.ps1` |
| Plugin | github@openai-curated | user | `~/.codex/config.toml` | Codex plugin | enabled |
| Setting | model | user | `~/.codex/config.toml` | default model | `gpt-5-codex` |
