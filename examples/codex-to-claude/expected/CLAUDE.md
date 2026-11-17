# tilecache

Map tile cache service. Python 3.12, uv.

- Run tests with `uv run pytest -q`.
- Use the `docs` MCP server for API questions.
- Never commit files under `data/`.

## Project history (carried over)

Carried over from Codex on 2026-03-10. Details: [decisions](carryover/decisions.md), [lessons](carryover/lessons.md), [tried and dropped](carryover/tried-and-dropped.md), [open threads](carryover/open-threads.md).

- Cache format is Parquet, not CSV (load time 40 s → 3 s).
- Do not use SQLite for the cache: concurrent writes fail with "database is locked".
- Tile keys are always joined with `/` (`posixpath`), never `os.path.join`.
- Open: LRU eviction is half-written.
