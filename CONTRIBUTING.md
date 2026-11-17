# Contributing

## Adding a tool (adapter)

1. Copy `skills/carryover/adapters/_template.md` to `adapters/<tool>.md` and fill it **from a real install**. Mark each row `L` (seen locally, with version) or `U` (docs only).
2. If the tool stores transcripts in a format the extractor can't read, add one reader function to `scripts/extract_history.py` (standard library only), plus:
   - a synthetic fixture under `examples/` (never real transcripts; no names, paths or content from real projects),
   - tests in `tests/` covering: text kept, tool output / injected context / subagent threads dropped, project path matching, redaction.
3. Add the tool's rows to `references/mapping.md`.

## Fixing a mapping

Say where the fact comes from: the file and version you saw, or a docs link. Rows without a source stay `U`.

## Running tests

```
python -X utf8 -m unittest discover -s tests -v
```

## Privacy

Pull requests must not contain real session logs, memory files, tokens or personal paths. The extractor's redaction is a safety net, not a guarantee.
