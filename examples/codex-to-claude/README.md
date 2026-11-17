# Example: Codex → Claude Code (synthetic)

Fictional project `tilecache` at `/work/tilecache`. Nothing here comes from a real user.

- `codex-home/`: a fake `~/.codex` (config, shell rules, three rollout files; one belongs to another project and must be ignored).
- `project/`: the repo as it was under Codex (`AGENTS.md`, `.codex/config.toml`).
- `expected/`: what the skill should produce in the repo (`CLAUDE.md`, `.mcp.json`, `.claude/settings.json`, `carryover/`).

Try the extractor:

```
python skills/carryover/scripts/extract_history.py --tool codex --home examples/codex-to-claude/codex-home --project /work/tilecache
```

(Git Bash on Windows rewrites `/work/...`; prefix with `MSYS_NO_PATHCONV=1`.)

To try the whole skill, copy `project/` somewhere, open it in Claude Code with the skill installed and say: "I moved this project from Codex, carry it over. Codex data is in <path>/codex-home." Compare with `expected/`.
