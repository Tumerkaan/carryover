# Example: Claude Code → Codex (synthetic)

`claude-home/` is a fake `~/.claude` with one transcript for `/work/tilecache`. It contains thinking blocks, tool calls, a side-chain message, a meta message, a compaction summary and a pasted key. The extractor must keep only the conversation text and the summary, with the key redacted:

```
python skills/carryover/scripts/extract_history.py --tool claude --home examples/claude-to-codex/claude-home --project /work/tilecache
```

Expected distilled result: one decision ("render queue stays on SQLite; Redis postponed, ~2k jobs/day does not justify a new service").
