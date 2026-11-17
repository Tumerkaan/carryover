#!/usr/bin/env python3
"""Blind question test for a carryover bundle.

For each question, two fresh `claude -p` sessions answer it:
  bundle   : its working folder holds the bundle (the instruction file + carryover/)
  baseline : an empty working folder
Both read the project through --add-dir with read-only tools. User-level settings (hooks,
plugins) are not loaded, no MCP server starts, no session is saved. Each question's answers
are written as X / Y in random order to answers.md; the key goes to a separate file that
judges must not open.

Usage:
  python -X utf8 blind_qa.py --bundle DIR --project DIR --questions FILE --out DIR [--dry]
  python -X utf8 blind_qa.py ... --only 1          one question, as a trial
  python -X utf8 blind_qa.py score --key KEY.json --scores SCORES.json
The questions file is Markdown; every line starting with "- " under "## Questions"
(or "## Sorular") is one question. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

HINT = ("You are working on the project folder {project}. You can only read. Answer for this project, "
        "briefly and concretely (at most 200 words). Say where you are unsure. Do not say which file or "
        "note the information came from; give the information itself. Answer in the question's language.")
TOOLS = ["Read", "Grep", "Glob"]
BLOCKED = ["Bash", "PowerShell", "Edit", "Write", "NotebookEdit", "WebFetch", "WebSearch", "Agent"]
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")


def read_questions(path: str) -> list:
    out, inside = [], False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            inside = line.strip().lower() in ("## questions", "## sorular")
            continue
        if inside and line.startswith("- ") and line[2:].strip():
            out.append(line[2:].strip())
    return out


def setup(root: str, bundle: str) -> dict:
    """Two working folders outside any repo, so no parent instruction file leaks in."""
    with_b, base = os.path.join(root, "bundle"), os.path.join(root, "baseline")
    os.makedirs(with_b)
    os.makedirs(base)
    for name in INSTRUCTION_FILES:
        if os.path.isfile(os.path.join(bundle, name)):
            shutil.copy2(os.path.join(bundle, name), with_b)
    shutil.copytree(os.path.join(bundle, "carryover"), os.path.join(with_b, "carryover"))
    return {"bundle": with_b, "baseline": base}


def command(question: str, project: str, model: str | None) -> list:
    cmd = ["claude", "-p", question, "--add-dir", project, "--allowedTools", *TOOLS,
           "--disallowedTools", *BLOCKED, "--setting-sources", "project", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "json",
           "--append-system-prompt", HINT.format(project=project)]
    return cmd + (["--model", model] if model else [])


def ask(cmd: list, cwd: str, timeout: int) -> dict:
    t = time.time()
    exe = shutil.which("claude") or "claude"
    try:
        r = subprocess.run([exe] + cmd[1:], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"answer": "(timeout)", "sec": round(time.time() - t), "error": True, "usd": None}
    try:
        j = json.loads(r.stdout)
        return {"answer": (j.get("result") or "").strip() or "(empty answer)", "sec": round(time.time() - t),
                "error": bool(j.get("is_error")), "usd": j.get("total_cost_usd")}
    except json.JSONDecodeError:
        return {"answer": "(unreadable output) " + (r.stderr or r.stdout)[-500:],
                "sec": round(time.time() - t), "error": True, "usd": None}


def run(a) -> int:
    qs = read_questions(a.questions)
    if not qs:
        sys.exit("no questions found")
    chosen = [x for x in enumerate(qs, 1) if not a.only or x[0] == a.only]
    for d in (a.bundle, a.project):
        if not os.path.isdir(d):
            sys.exit(f"not found: {d}")
    if not os.path.isdir(os.path.join(a.bundle, "carryover")):
        sys.exit("the bundle folder needs a carryover/ subfolder")
    if a.dry:
        print(f"{len(chosen)} questions, two sessions each")
        print(" ".join(f'"{x}"' if " " in x else x for x in command(chosen[0][1], a.project, a.model)))
        return 0
    os.makedirs(a.out, exist_ok=True)
    root = tempfile.mkdtemp(prefix="carryover-blind-")
    dirs = setup(root, a.bundle)
    rng = random.Random(a.seed)
    key, lines = {}, ["# Answers", "",
                      "Score X and Y 0/1/2 for each question, then say which is better (X, Y or equal).", ""]
    try:
        for i, q in chosen:
            res = {}
            for side in ("bundle", "baseline"):
                print(f"[{i}/{len(qs)}] {side} ...", file=sys.stderr, flush=True)
                res[side] = ask(command(q, a.project, a.model), dirs[side], a.timeout)
            order = ["bundle", "baseline"]
            rng.shuffle(order)
            key[str(i)] = {"X": order[0], "Y": order[1], **{s: {k: v for k, v in res[s].items() if k != "answer"}
                                                             for s in order}}
            lines += [f"## Question {i}", "", q, "", "### X", "", res[order[0]]["answer"], "",
                      "### Y", "", res[order[1]]["answer"], ""]
    finally:
        shutil.rmtree(root, ignore_errors=True)
    open(os.path.join(a.out, "answers.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    open(os.path.join(a.out, ".key.json"), "w", encoding="utf-8").write(json.dumps(key, indent=2))
    print(f"wrote {os.path.join(a.out, 'answers.md')} (key in .key.json; keep it from judges)", file=sys.stderr)
    return 0


def score(a) -> int:
    """scores.json: {"judge name": [[x, y, "X"|"Y"|"="], ...one per question]}"""
    key = json.load(open(a.key, encoding="utf-8"))
    judges = json.load(open(a.scores, encoding="utf-8"))
    print("| Judge | Bundle | Baseline | Bundle better | Baseline better | Equal |")
    print("|---|---|---|---|---|---|")
    for name, rows in judges.items():
        t = {"bundle": 0, "baseline": 0, "better_bundle": 0, "better_baseline": 0, "equal": 0}
        for i, (x, y, better) in enumerate(rows, 1):
            k = key[str(i)]
            t[k["X"]] += x
            t[k["Y"]] += y
            t["equal" if better == "=" else "better_" + k[better]] += 1
        top = 2 * len(rows)
        print(f"| {name} | {t['bundle']}/{top} | {t['baseline']}/{top} | {t['better_bundle']} | "
              f"{t['better_baseline']} | {t['equal']} |")
    for side in ("bundle", "baseline"):
        sec = sum(v[side]["sec"] for v in key.values())
        usd = sum(v[side]["usd"] or 0 for v in key.values())
        print(f"{side}: {sec} s, ${usd:.2f}")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["score"]:
        sp = argparse.ArgumentParser(prog="blind_qa.py score")
        sp.add_argument("--key", required=True)
        sp.add_argument("--scores", required=True)
        return score(sp.parse_args(argv[1:]))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", required=True, help="folder with CLAUDE.md/AGENTS.md and carryover/")
    ap.add_argument("--project", required=True, help="the project, read only")
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out", required=True, help="where answers.md and .key.json go")
    ap.add_argument("--only", type=int, help="run only this question number (1-based)")
    ap.add_argument("--model", help="same model for both sides (default: claude's default)")
    ap.add_argument("--timeout", type=int, default=600, help="seconds per session")
    ap.add_argument("--seed", type=int, help="shuffle seed (default: random)")
    ap.add_argument("--dry", action="store_true", help="print the command, run nothing")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
