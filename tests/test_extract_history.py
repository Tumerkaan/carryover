"""Tests for skills/carryover/scripts/extract_history.py on synthetic fixtures.

Run: python -m unittest discover -s tests -v
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "carryover", "scripts"))
import extract_history as eh  # noqa: E402

CODEX_HOME = os.path.join(ROOT, "examples", "codex-to-claude", "codex-home")
CLAUDE_HOME = os.path.join(ROOT, "examples", "claude-to-codex", "claude-home")
PROJECT = "/work/tilecache"


def digest(tool, home, project=PROJECT, **kw):
    msgs = eh.collect(tool, home, project, kw.get("since"))
    return msgs, eh.render(msgs, tool, project, kw.get("per_msg", 2000), kw.get("max_chars", 200_000))


class CodexJsonl(unittest.TestCase):
    def setUp(self):
        self.msgs, self.text = digest("codex", CODEX_HOME)

    def test_keeps_user_and_agent_text(self):
        self.assertIn("Parquet'i denedim", self.text)
        self.assertIn("posixpath", self.text)

    def test_keeps_compaction_summary(self):
        self.assertTrue(any(m.role == "summary" for m in self.msgs))
        self.assertIn("LRU temizleme", self.text)

    def test_drops_noise(self):
        for marker in ("DEVELOPER_TEXT", "INJECTED", "REASONING", "TOOL_OUTPUT", "OTHER_PROJECT"):
            self.assertNotIn(marker, self.text, marker)

    def test_subdirectory_counts_as_project(self):
        self.assertEqual({m.session for m in self.msgs}, {"s1", "s2"})

    def test_redacts_token(self):
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz0123", self.text)
        self.assertIn("[REDACTED]", self.text)

    def test_utf8_and_order(self):
        self.assertIn("Önbelleği", self.text)
        ts = [m.timestamp for m in self.msgs]
        self.assertEqual(ts, sorted(ts))

    def test_since_filter(self):
        msgs, _ = digest("codex", CODEX_HOME, since="2026-03-05")
        self.assertEqual({m.session for m in msgs}, {"s2"})


class ClaudeJsonl(unittest.TestCase):
    def setUp(self):
        self.msgs, self.text = digest("claude", CLAUDE_HOME)

    def test_keeps_text(self):
        self.assertIn("Redis'e taşıyalım", self.text)
        self.assertIn("ertelemeyi öneririm", self.text)

    def test_drops_noise(self):
        for marker in ("REMINDER", "THINKING", "TOOL_RESULT", "SIDECHAIN", "META_SHOULD"):
            self.assertNotIn(marker, self.text, marker)

    def test_compact_summary_kept(self):
        self.assertEqual([m.role for m in self.msgs].count("summary"), 1)

    def test_redacts_key(self):
        self.assertNotIn("sk-ant-abcdefghijklmnopqrstuv1234", self.text)

    def test_other_project_empty(self):
        msgs, _ = digest("claude", CLAUDE_HOME, project="/work/other")
        self.assertEqual(msgs, [])


class CodexSqlite(unittest.TestCase):
    """Synthetic SQLite store shaped like the one observed in Codex Desktop 0.16x."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        home = self.tmp.name
        s = sqlite3.connect(os.path.join(home, "state_5.sqlite"))
        s.execute("create table threads (id text, cwd text, source text, rollout_path text)")
        s.execute("create table thread_spawn_edges (parent_thread_id text, child_thread_id text, status text)")
        s.executemany("insert into threads values (?,?,?,?)", [
            ("t-main", "/work/tilecache", "vscode", None),
            ("t-sub", "/work/tilecache", '{"subagent":{"thread_spawn":{}}}', None),
            ("t-child", "/work/tilecache", "vscode", None),
            ("t-other", "/work/elsewhere", "vscode", None),
        ])
        s.execute("insert into thread_spawn_edges values ('t-main','t-child','done')")
        s.commit(); s.close()
        h = sqlite3.connect(os.path.join(home, "thread_history_1.sqlite"))
        h.execute("create table thread_items (thread_id text, turn_id text, item_id text, rollout_ordinal int,"
                  " created_at_ms int, item_json text, item_type text)")

        def user(t):
            return json.dumps({"type": "userMessage", "content": [{"type": "text", "text": t}]})

        def agent(t, phase="final_answer"):
            return json.dumps({"type": "agentMessage", "text": t, "phase": phase})

        base = 1772445600000  # 2026-03-02
        rows = [
            ("t-main", 1, user("<heartbeat>\n<automation>INJECTED_HEARTBEAT</automation>\n</heartbeat>"), "userMessage"),
            ("t-main", 2, user("# In app browser:\n- INJECTED_BROWSER\n\n## My request for Codex:\nCache'i Parquet'e çevir."), "userMessage"),
            ("t-main", 3, agent("COMMENTARY_SHOULD_NOT_APPEAR", "commentary"), "agentMessage"),
            ("t-main", 4, json.dumps({"type": "commandExecution", "command": "TOOL_SHOULD_NOT_APPEAR"}), "commandExecution"),
            ("t-main", 5, agent("Parquet'e geçildi; SQLite kilitlendiği için bırakıldı."), "agentMessage"),
            ("t-sub", 1, user("SUBAGENT_SHOULD_NOT_APPEAR"), "userMessage"),
            ("t-child", 1, user("CHILD_SHOULD_NOT_APPEAR"), "userMessage"),
            ("t-other", 1, user("OTHER_SHOULD_NOT_APPEAR"), "userMessage"),
        ]
        h.executemany("insert into thread_items values (?,?,?,?,?,?,?)",
                      [(t, "turn", f"{t}-{o}", o, base + o * 1000, j, ty) for t, o, j, ty in rows])
        h.commit(); h.close()
        self.msgs, self.text = digest("codex", home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_main_thread(self):
        self.assertEqual({m.session for m in self.msgs}, {"t-main"})
        self.assertIn("Cache'i Parquet'e çevir.", self.text)
        self.assertIn("SQLite kilitlendiği", self.text)

    def test_drops_noise(self):
        for marker in ("INJECTED", "COMMENTARY", "TOOL_SHOULD", "SUBAGENT", "CHILD", "OTHER_SHOULD"):
            self.assertNotIn(marker, self.text, marker)

    def test_timestamp(self):
        self.assertTrue(self.msgs[0].timestamp.startswith("2026-03-02"))


class Limits(unittest.TestCase):
    def test_max_chars_truncates(self):
        _, text = digest("codex", CODEX_HOME, max_chars=500)
        self.assertIn("digest truncated", text)

    def test_per_message_cap(self):
        _, text = digest("codex", CODEX_HOME, per_msg=20)
        self.assertIn("[...]", text)

    def test_redact_patterns(self):
        self.assertEqual(eh.redact("password=hunter2xyz"), "password=[REDACTED]")
        self.assertIn("[REDACTED]", eh.redact("Authorization: Bearer abcdefghijklmnop"))
        self.assertEqual(eh.redact("tokens used: 1234"), "tokens used: 1234")


if __name__ == "__main__":
    unittest.main()
