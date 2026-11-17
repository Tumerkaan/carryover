"""Tests for evals/blind_qa.py (no claude calls)."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "evals"))
import blind_qa as bq  # noqa: E402


class BlindQa(unittest.TestCase):
    def test_reads_questions_section_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "q.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# T\n- not this\n## Sorular\n- Bir mi?\n- \n- İki mi?\n## Other\n- no\n")
            self.assertEqual(bq.read_questions(p), ["Bir mi?", "İki mi?"])

    def test_setup_copies_bundle_only(self):
        with tempfile.TemporaryDirectory() as d:
            b = os.path.join(d, "b")
            os.makedirs(os.path.join(b, "carryover"))
            open(os.path.join(b, "CLAUDE.md"), "w").write("x")
            open(os.path.join(b, "carryover", "decisions.md"), "w").write("y")
            open(os.path.join(b, "notes.txt"), "w").write("z")
            dirs = bq.setup(os.path.join(d, "run"), b)
            self.assertEqual(sorted(os.listdir(dirs["bundle"])), ["CLAUDE.md", "carryover"])
            self.assertEqual(os.listdir(dirs["baseline"]), [])

    def test_command_is_read_only(self):
        cmd = bq.command("q?", "/p", None)
        self.assertIn("--setting-sources", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project")
        for tool in ("Bash", "Edit", "Write"):
            self.assertIn(tool, cmd[cmd.index("--disallowedTools"):])

    def test_score_unshuffles(self):
        with tempfile.TemporaryDirectory() as d:
            key = {"1": {"X": "bundle", "Y": "baseline", "bundle": {"sec": 10, "usd": 0.1},
                         "baseline": {"sec": 20, "usd": 0.2}},
                   "2": {"X": "baseline", "Y": "bundle", "bundle": {"sec": 10, "usd": 0.1},
                         "baseline": {"sec": 20, "usd": 0.2}}}
            scores = {"j": [[2, 1, "X"], [0, 2, "Y"]]}
            kp, sp = os.path.join(d, "k.json"), os.path.join(d, "s.json")
            json.dump(key, open(kp, "w"))
            json.dump(scores, open(sp, "w"))
            buf = io.StringIO()
            with redirect_stdout(buf):
                bq.main(["score", "--key", kp, "--scores", sp])
            self.assertIn("| j | 4/4 | 1/4 | 2 | 0 | 0 |", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
