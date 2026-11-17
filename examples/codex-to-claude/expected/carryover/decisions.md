# Decisions

## Tile keys are joined with "/" on every OS
- When: 2026-03-09 (codex session)
- What: Tile cache keys are built with `posixpath.join`.
- Why: `os.path.join` produced backslashes on Windows and broke tests.
- Applies to: src/cache/

## Cache is stored as Parquet
- When: 2026-03-02 (codex session)
- What: The cache layer writes Parquet (src/cache/store.py).
- Why: Full-dataset load went from 40 s (CSV) to 3 s, and column types are kept.
- Applies to: src/cache/store.py
