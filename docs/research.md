# Gap analysis (2026-11-17)

Where existing tools stop when moving a project between AI coding tools. Web sources are mostly third-party blogs; the WebFetch step was blocked in the research environment, so web claims come from search summaries and are marked as such. Local checks were done on Claude Code 2.1.318 and Codex Desktop 0.167.0-alpha (Windows).

## 1. Instruction files: solved

- `AGENTS.md` is the shared convention; Codex reads it natively, Claude Code reads `CLAUDE.md` (which can import `@AGENTS.md`).
- ruler (`.ruler/` → each tool's files, incl. MCP) and rulesync (`.rulesync/` → native files, also MCP and skills) generate per-tool files from one source. [developertoolkit.ai overview](https://developertoolkit.ai/en/ecosystem/frameworks/rules-sync/) (search summary)

## 2. Claude Code → Codex: largely covered officially

- OpenAI ships a `migrate-to-codex` skill (Apache-2.0, part of the curated `openai/skills` set, read locally). It converts instructions, commands → skills, skills, MCP, hooks (command type only, shell-only matching) and subagents. Plugins are reported for manual work. **It does not touch session history.** Its `references/differences.md` is the most detailed public mapping for this direction.
- Codex CLI `/import` (since ~0.140, expanded in 0.145) is reported to carry settings, skills, MCP, memories and recent chats (~30 days). [Vaughan, v0.145](https://codex.danielvaughan.com/2026/07/24/codex-cli-v0145-import-command-cursor-claude-code-migration-mcp-servers-memories-settings/), [thepromptshelf](https://thepromptshelf.dev/blog/openai-codex-import-claude-code-migration-2026/), [memorylake](https://www.memorylake.ai/en/blogs/migrate-claude-code-to-codex) (search summaries; versions unverified)

## 3. Codex → Claude Code: no official path

- No Anthropic importer found.
- Community tools convert raw transcripts: cx2cc, cc-sync, transession. Both transcript formats are undocumented internals, so these break when the CLIs change. [transession](https://docs.rs/crate/transession/0.1.2/source/README.md), [cx2cc](https://www.pkgstats.com/pkg:cx2cc) (search summaries)

## 4. History distillation: nobody does it

Every path above either copies raw chats or ignores them. None of them extracts *why* a decision was made, what was tried and abandoned, or what was left half-done. That is carryover's core.

## 5. Silent loss in settings mapping

Existing converters skip what has no equivalent. For the Codex → Claude direction nobody reports it at all. Examples: Codex `enabled_tools` per MCP server, `startup_timeout_sec`, `rules/*.rules` prefix rules, `notify`, plugins; Claude prompt/agent/http hooks, `Notification` and `PreCompact` hooks, `settings.local.json`.

## Local findings that change the design

- **Codex history moved to SQLite.** On the checked Codex Desktop install, ~3000 threads were listed in `state_5.sqlite` but only 1 rollout `.jsonl` remained on disk. Messages live in `thread_history_1.sqlite` → `thread_items`. Tools that only read `~/.codex/sessions/*.jsonl` see almost nothing on such installs.
- **Claude Code deletes transcripts** after `cleanupPeriodDays` (default 30). Leaving Claude Code late means older history is already gone; distilled memory (`~/.claude/projects/<p>/memory/`) survives.
- **Codex memories are global**, not per project (`~/.codex/memories/`, `rollout_summaries/<date>-<slug>.md`), so they must be filtered by topic.
- **Injected context is everywhere.** Codex app messages wrap the user's words in `# In app browser:` / `## My request for Codex:` blocks and `<heartbeat>` automation pings. Claude transcripts carry `<system-reminder>` blocks. A digest must strip these or the distillation is mostly noise.

## Other tools (not yet adapters)

- GLM (Z.ai coding plan) and Kimi models are commonly used **inside** Claude Code via Anthropic-compatible endpoints; CLAUDE.md and MCP keep working, nothing to migrate. [Z.ai docs](https://docs.z.ai/devpack/overview), [hyscaler review](https://hyscaler.com/insights/glm-coding-plan-review) (search summaries)
- Qwen Code, Kimi CLI and Gemini CLI are separate tools and need adapters; not verified here.
