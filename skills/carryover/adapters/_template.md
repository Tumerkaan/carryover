# Adapter template (for a tool without an adapter yet)

Use this for Qwen Code, Kimi CLI, Gemini CLI, OpenCode, Cursor, or any other agent. Fill it **by discovery on the user's machine and the tool's own docs**, not from memory. Mark every row `L` (seen locally, with version) or `U` (from docs only). Contributions back to the repo are welcome: save the filled file as `adapters/<tool>.md`.

## 1. Discovery

- [ ] Tool version: `<tool> --version`
- [ ] Data directory in home (look for `~/.<tool>`, `%APPDATA%\<tool>`, `~/.config/<tool>`): ...
- [ ] Project-level folder (`.<tool>/` in the repo?): ...
- [ ] Does it read `AGENTS.md`? Its own file name (e.g. `<TOOL>.md`)?: ...
- [ ] Is it a fork of another tool (then start from that tool's adapter)?: ...

## 2. Where things live

| What | Project | User | Src |
| --- | --- | --- | --- |
| Instructions | | | |
| Config / settings file | | | |
| MCP servers | | | |
| Permission / approval rules | | | |
| Hooks | | | |
| Subagents | | | |
| Commands / prompts | | | |
| Skills | | | |
| Memory | | | |
| Session transcripts (path + retention) | | | |

## 3. Transcript format

Open one small session file and record **keys and types only** (do not paste content):
- [ ] One file per session? JSONL / JSON / SQLite?
- [ ] Field holding the project directory: ...
- [ ] How a user message looks: ...
- [ ] How an assistant message looks: ...
- [ ] Injected/system messages to drop: ...
- [ ] Compaction/summary records to keep: ...

If the format is JSONL, add a reader to `scripts/extract_history.py` (one function, plus a synthetic fixture and a test).

## 4. Official importer

- [ ] Does the tool have an import/migration command? What does it carry?

## 5. Writing

- [ ] Preferred CLI commands for adding MCP servers / skills (so the tool writes its own files).
