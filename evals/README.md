# Measuring a bundle

Passing tests says the extractor works. Whether the bundle actually helps is a different question. This is the protocol used on the first real project (Codex → Claude Code). It has three measurements; each catches a different failure.

The judge needs a source of truth. Best is the person who worked on the project. If that is not possible, an independent model can re-read the raw history and the project (not the bundle) and act as the reference. Say which one you used when you report numbers.

## 1. Recall: what did the bundle miss?

Before anyone reads the bundle, the reference writes the 8–10 things a new agent must know and would otherwise get wrong (decisions with their reason, dead ends, lessons, open threads). Use the skill's own quality bar: only what is not visible in code, git history or tracked docs. Then check each item against the bundle: **full / partial / missing**.

Measure: share of items covered (partial counts as half).

## 2. Precision: is what it wrote right and worth it?

Label every bundle entry:

- **Important**: correct, and a new agent would get it wrong otherwise.
- **Unneeded**: correct but obvious, trivial, historical, or already in tracked docs.
- **Distorted**: partly right but misleading (stale number, wrong path, a superseded decision).
- **Wrong**: fabricated or contradicts the source.

Every Distorted or Wrong label needs evidence (`file:line` in the history or the project). Spot-check them yourself.

Measure: share of Important entries, and the count of Distorted + Wrong (a wrong detail is repeated by the agent that trusts it).

## 3. Blind questions: does it help an agent?

Write 8–10 questions a new agent would face on this project, phrased so they do not give the answer away. Mix: why was X done this way, was Y tried, what is the current state, what should happen next, an environment trap. Then:

```
python -X utf8 evals/blind_qa.py --bundle <folder with CLAUDE.md + carryover/> --project <project> \
    --questions questions.md --out <results dir> --only 1     # trial: read both answers first
python -X utf8 evals/blind_qa.py --bundle ... --project ... --questions questions.md --out <results dir>
```

Each question goes to two fresh `claude -p` sessions, with and without the bundle, both read-only on the project. Answers land in `answers.md` as X / Y in random order per question; `.key.json` says which is which.

Run the trial first and check two things. The session without the bundle must really read the project; otherwise the bundle wins trivially. Neither answer may name `carryover/` or the instruction file, since that breaks the blinding.

Judges score each answer 0/1/2 (wrong or misleading / partly right / right for this project) and say which is better. Use more than one judge and report where they agree. A judge must not have seen the bundle, and should read `answers.md` from a copy outside the bundle folder: tools that auto-load a folder's instruction file would show it the bundle. Then:

```
python -X utf8 evals/blind_qa.py score --key <results dir>/.key.json --scores scores.json
```

`scores.json` maps each judge to one `[x, y, "X"|"Y"|"="]` per question. The key is shuffled per question, so X and Y totals alone mean nothing.

Cost on the first project: about $0.40 per question for both sessions.

## Privacy

Answers, digests and judge notes contain project content. Keep them outside the repo, or in a git-ignored folder, and delete raw digests when done.
