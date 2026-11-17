"""The example's expected destination files must be valid config."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples", "codex-to-claude")


class ExpectedFiles(unittest.TestCase):
    def test_json_parses(self):
        for rel in ("expected/.mcp.json", "expected/.claude/settings.json"):
            with open(os.path.join(EX, rel), encoding="utf-8") as fh:
                json.load(fh)

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib needs Python 3.11+")
    def test_toml_parses(self):
        import tomllib
        for rel in ("codex-home/config.toml", "project/.codex/config.toml"):
            with open(os.path.join(EX, rel), "rb") as fh:
                tomllib.load(fh)

    def test_no_secret_values_in_expected(self):
        for dirpath, _, files in os.walk(os.path.join(EX, "expected")):
            for f in files:
                text = open(os.path.join(dirpath, f), encoding="utf-8").read()
                self.assertNotIn("ghp_", text, f)
                self.assertNotIn("sk-", text, f)


if __name__ == "__main__":
    unittest.main()
