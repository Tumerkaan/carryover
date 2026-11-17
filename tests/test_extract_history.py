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
        for marker in ("REMINDER", "THINKING", "TOOL_RESULT", "SIDECHAIN", "META_SHOULD", "TASK_NOTIFICATION"):
            self.assertNotIn(marker, self.text, marker)

    def test_compact_summary_kept(self):
        self.assertEqual([m.role for m in self.msgs].count("summary"), 1)

    def test_redacts_key(self):
        self.assertNotIn("sk-ant-abcdefghijklmnopqrstuv1234", self.text)

    def test_tag_with_attributes_stripped_text_kept(self):
        self.assertIn("Kuyruğa öncelik alanı ekle.", self.text)

    def test_old_location_needs_explicit_path(self):
        self.assertNotIn("Eski klasördeyken", self.text)
        msgs, text = digest("claude", CLAUDE_HOME, project=[PROJECT, "/old/tilecache"])
        self.assertIn("Eski klasördeyken", text)
        self.assertEqual(msgs[0].timestamp[:10], "2026-04-20")

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
            ("t-main", "hb", 1, user("<heartbeat>\n<automation>INJECTED_HEARTBEAT</automation>\n</heartbeat>"), "userMessage"),
            ("t-main", "hb", 2, agent("HEARTBEAT_REPLY_SHOULD_NOT_APPEAR"), "agentMessage"),
            ("t-main", "u1", 3, user("# In app browser:\n- INJECTED_BROWSER\n\n## My request for Codex:\nCache'i Parquet'e çevir."), "userMessage"),
            ("t-main", "u1", 4, user("# In app browser:\n- INJECTED_BROWSER\n\n## My request for Codex:\nCache'i Parquet'e çevir."), "userMessage"),
            ("t-main", "u1", 5, agent("COMMENTARY_SHOULD_NOT_APPEAR", "commentary"), "agentMessage"),
            ("t-main", "u1", 6, json.dumps({"type": "commandExecution", "command": "TOOL_SHOULD_NOT_APPEAR"}), "commandExecution"),
            ("t-main", "u1", 7, agent("Parquet'e geçildi; SQLite kilitlendiği için bırakıldı. Sorular: dev@example.com\n# Başlık"), "agentMessage"),
            ("t-main", "loop", 8, agent("Otonom tur: sprint 12 bitti."), "agentMessage"),
            ("t-sub", "s", 1, user("SUBAGENT_SHOULD_NOT_APPEAR"), "userMessage"),
            ("t-child", "c", 1, user("CHILD_SHOULD_NOT_APPEAR"), "userMessage"),
            ("t-other", "o", 1, user("OTHER_SHOULD_NOT_APPEAR"), "userMessage"),
        ]
        h.executemany("insert into thread_items values (?,?,?,?,?,?,?)",
                      [(t, turn, f"{t}-{o}", o, base + o * 1000, j, ty) for t, turn, o, j, ty in rows])
        h.commit(); h.close()
        self.msgs, self.text = digest("codex", home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_main_thread(self):
        self.assertEqual({m.session for m in self.msgs}, {"t-main"})
        self.assertIn("Cache'i Parquet'e çevir.", self.text)
        self.assertIn("SQLite kilitlendiği", self.text)

    def test_drops_noise(self):
        for marker in ("INJECTED", "COMMENTARY", "TOOL_SHOULD", "SUBAGENT", "CHILD", "OTHER_SHOULD", "HEARTBEAT_REPLY"):
            self.assertNotIn(marker, self.text, marker)

    def test_duplicate_dropped_email_masked_heading_escaped(self):
        self.assertEqual(self.text.count("Cache'i Parquet'e çevir."), 1)
        self.assertNotIn("dev@example.com", self.text)
        self.assertIn("[EMAIL]", self.text)
        self.assertIn("\\# Başlık", self.text)

    def test_agent_turn_without_user_is_auto(self):
        roles = {m.text: m.role for m in self.msgs}
        self.assertEqual(roles["Otonom tur: sprint 12 bitti."], "auto")
        self.assertIn("**AUTO**", self.text)
        dropped = eh.collect("codex", self.tmp.name, PROJECT, None, None, None, True)
        self.assertNotIn("auto", {m.role for m in dropped})

    def test_exclude_session(self):
        msgs = eh.collect("codex", self.tmp.name, PROJECT, None, None, ["t-main"])
        self.assertEqual(msgs, [])

    def test_timestamp(self):
        self.assertTrue(self.msgs[0].timestamp.startswith("2026-03-02"))


class Limits(unittest.TestCase):
    def test_max_chars_truncates(self):
        _, text = digest("codex", CODEX_HOME, max_chars=500)
        self.assertIn("TRUNCATED", text)

    def test_parts_cover_everything(self):
        msgs, _ = digest("codex", CODEX_HOME)
        parts = eh.render_parts(msgs, "codex", PROJECT, 2000, 600)
        self.assertGreater(len(parts), 1)
        joined = "".join(parts)
        for m in msgs:
            self.assertIn(eh._body(m.text, 2000)[:30], joined)
        self.assertIn("part 1 of", parts[0])
        self.assertIn("### 2026-03-09", joined)

    def test_out_writes_numbered_parts(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "dig.md")
            eh.main(["--tool", "codex", "--home", CODEX_HOME, "--project", PROJECT, "--max-chars", "600", "--out", out])
            self.assertTrue(os.path.exists(os.path.join(d, "dig-01.md")))
            self.assertTrue(os.path.exists(os.path.join(d, "dig-02.md")))

    def test_per_message_cap(self):
        _, text = digest("codex", CODEX_HOME, per_msg=20)
        self.assertIn("[...]", text)

    def test_windows_extended_prefix(self):
        self.assertTrue(eh.in_project(r"\\?\C:\Users\x\Proje Ğ\src", r"C:\Users\x\Proje Ğ"))
        self.assertTrue(eh.in_project(r"C:\Users\x\proj", r"\\?\C:\Users\x\proj"))
        self.assertFalse(eh.in_project(r"\\?\C:\Users\x\proj2", r"C:\Users\x\proj"))

    def test_redact_patterns(self):
        self.assertEqual(eh.redact("password=hunter2xyz"), "password=[REDACTED]")
        self.assertIn("[REDACTED]", eh.redact("Authorization: Bearer abcdefghijklmnop"))
        self.assertEqual(eh.redact("tokens used: 1234"), "tokens used: 1234")

    def test_parts_never_exceed_max_chars(self):
        msgs = [eh.Msg("s", f"2026-01-{1 + i % 28:02d}T10:00:00Z", "user", "öğün " * 300) for i in range(60)]
        parts = eh.render_parts(msgs, "codex", PROJECT, 2000, 10_000)
        self.assertGreater(len(parts), 5)
        for p in parts:
            self.assertLessEqual(len(p), 10_000)
            self.assertIn("## session s", p)  # each part says which session it continues

    def test_home_dir_user_masked(self):
        self.assertEqual(eh.redact(r"C:\Users\alice\proj"), r"C:\Users\<user>\proj")
        self.assertEqual(eh.redact("/home/bob/x and /Users/carol/y"), "/home/<user>/x and /Users/<user>/y")
        self.assertEqual(eh.redact("`c:/users/dave/p`"), "`c:/users/<user>/p`")
        self.assertEqual(eh.redact("cd /mnt/c/Users/eve/p; ls /c/Users/eve"), "cd /mnt/c/Users/<user>/p; ls /c/Users/<user>")
        for keep in ("src/users/models.py", "GET /api/users/42", "https://site.org/home/page",
                     "app\\users\\views.py"):
            self.assertEqual(eh.redact(keep), keep)


class LongTokensAndNames(unittest.TestCase):
    def tearDown(self):
        eh.set_masks([])

    def test_url_query_cut_address_kept(self):
        url = "https://help.example.com/hc/articles/123-reset-password?" + "q=" + "a" * 400
        out = eh._body("see " + url, 2000)
        self.assertIn("https://help.example.com/hc/articles/123-reset-password?[...query cut]", out)

    def test_url_in_markdown_link_kept(self):
        url = "https://help.example.com/hc/en/articles/" + "-".join(["slug"] * 40) + "?x=" + "b" * 80
        out = eh._body(f"[Help]({url})", 2000)
        self.assertIn("[Help](https://help.example.com/hc/en/articles/slug-", out)
        self.assertNotIn("long token cut", out)

    def test_blob_still_cut(self):
        out = eh._body("data:" + "A" * 500, 2000)
        self.assertIn("[...long token cut]", out)

    def test_names_masked(self):
        used = eh.set_masks(["Ayşe Yılmaz", "dependabot[bot]", "Claude", "jdoe"])
        self.assertEqual(used, ["Ayşe Yılmaz", "jdoe"])
        self.assertEqual(eh.redact("Ayşe Yılmaz, Yılmaz hoca, JDOE ve Ayşe"), "[NAME], [NAME] hoca, [NAME] ve [NAME]")
        self.assertEqual(eh.redact("Claude yazdı; yılmaz değil"), "Claude yazdı; yılmaz değil")

    def test_remote_owner_pattern(self):
        out = ("origin\thttps://github.com/acme-org/repo.git (fetch)\n"
               "up\tgit@gitlab.com:bob/x.git (push)\n")
        self.assertEqual(eh._REMOTE_OWNER.findall(out), ["acme-org", "bob"])

    def test_git_authors_skip_project_name_and_read_remote(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            proj = os.path.join(d, "myproj")
            os.makedirs(proj)
            git = lambda *a: subprocess.run(["git", "-C", proj, *a], check=True, capture_output=True)
            try:
                git("init", "-q")
            except (OSError, subprocess.CalledProcessError):
                self.skipTest("git not available")
            git("-c", "user.name=myproj", "-c", "user.email=a@b.c", "commit", "-q", "--allow-empty", "-m", "x")
            git("-c", "user.name=Jane Roe", "-c", "user.email=a@b.c", "commit", "-q", "--allow-empty", "-m", "y")
            git("remote", "add", "origin", "https://github.com/janeroe99/myproj.git")
            self.assertEqual(eh.git_authors([proj]), ["Jane Roe", "janeroe99"])

    def test_git_authors_of_non_repo_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(eh.git_authors([d, os.path.join(d, "missing")]), [])


if __name__ == "__main__":
    unittest.main()
