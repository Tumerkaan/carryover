# Tried and dropped

## SQLite as the cache store
- When: 2026-03-02 (codex session)
- Dropped because: concurrent writes failed with "database is locked".
- Would reconsider if: writes become single-process.

## CSV as the cache format
- When: 2026-03-02 (codex session)
- Dropped because: 40 s load on the full dataset; types lost.
