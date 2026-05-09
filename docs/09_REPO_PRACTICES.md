# 09 Repository Practices

> Engineering hygiene for this repo. Light enough for a 10-hour prototype, rigorous enough that a reviewer can read the commit history and trust it.

## Branching

For a solo prototype, use `main` only. No feature branches, no GitFlow.

If you want to experiment, use `git stash` or local branches that get deleted before push.

## Commits

One commit per build hour. The format is `[hour-N] short description`.

Examples:
- `[hour-1] initial repo setup`
- `[hour-2] mock customer, transaction, rules data`
- `[hour-3] synthetic certificate PDF generator`
- `[hour-5] agent orchestrator with tool use loop`

If you slip more than ~30 minutes within an hour, that's still one commit. The hours are a planning unit, not a strict measure.

For mid-hour checkpoints: don't commit. `git stash` if you need to switch contexts.

## Commit message conventions

- Title: 50 characters max, imperative mood ("add tests" not "added tests")
- Optional body: explain *why*, not *what* (the diff shows what)
- Reference docs where relevant: "implements docs/03 hour 5"

Bad: `[hour-5] stuff`
Good: `[hour-5] agent orchestrator with tool use loop`
Better: 
```
[hour-5] agent orchestrator with tool use loop

implements docs/03 hour 5: validate_certificate function with
hard 10-iteration cap, exponential backoff on transient errors,
and post-decision verifier for hallucinated rule_ids.
```

## File-level conventions

- Every Python file starts with a module docstring explaining what it does
- Every public function has a docstring with Args/Returns/Raises (Google style)
- Imports grouped: standard library, third-party, local
- No commented-out code in committed files (use git history instead)
- No `print()` in production code paths; use `logging`

Example module header:

```python
"""Agent orchestrator: runs Claude with tool use to validate certificates.

This module implements the agent loop that takes a certificate PDF and
customer ID and returns a structured Decision. It calls tools defined in
src/agent/tools.py and produces output validated by src/agent/verifier.py.
"""
```

## .gitignore

The provided `.gitignore` template covers:
- Python: `__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`
- Environment: `.env`, `.env.local`
- Logs: `logs/*.jsonl`
- Generated: `data/certificates/*.pdf` (regeneratable from script)
- IDE: `.vscode/settings.json`, `.idea/`
- OS: `.DS_Store`, `Thumbs.db`

Do NOT add `data/customers.json`, `data/transactions.json`, `data/rules.json` to gitignore. These are mock data that needs to be in the repo for reviewers.

Do NOT add `eval_scenarios/scenarios.json` to gitignore. The eval set is a deliverable.

## Pre-commit checks

Manual, run before each commit:

1. `git status` — review what's staged
2. Read the diff of staged files (`git diff --cached`)
3. Check no secrets are present: `git diff --cached | grep -i "sk-ant\|password\|secret"`
4. If you have time: `pytest` should pass before commit

Not running automated pre-commit hooks for the prototype. Good discipline manually is sufficient.

## Code style

- Use `ruff` if available: `pip install ruff`, then `ruff check src/` and `ruff format src/`
- Otherwise, follow PEP 8 by hand
- Line length: 100 characters max (ruff default)
- Double quotes for strings (ruff default)

Don't fight the tooling. If ruff says something is wrong, either fix it or add a `# noqa` with a reason.

## README in the actual repo

The repo's `README.md` is for reviewers landing from the share link. Different from this build package's README.

Should contain:
1. **One-paragraph project description**
2. **Live demo link** (with note that it's password-protected)
3. **Architecture diagram** (mermaid in README; GitHub renders it)
4. **Quick local setup** (4-5 commands)
5. **Project structure** (directory tree)
6. **How to read this repo** (point to `docs/`)
7. **What this is not** (explicit non-goals)
8. **Build budget note** (10 hours, 1 person, May 2026)
9. **License or "private prototype" note**

Do NOT include in the repo README:
- Anything about Vertex by name
- Real customer or company names
- Internal Anthropic info
- Apologies or hedges ("this is rough", "I didn't have time to..."). Stand behind the work.

## Issue tracking

Don't bother with GitHub Issues for a 10-hour prototype.

If you find a bug mid-build that you can't fix immediately, create a `TODO.md` at repo root with a numbered list. Resolve all TODOs by hour 10. Final commit removes `TODO.md` (or it ships in the repo as a `LIMITATIONS.md` honestly listing known issues).

## Pull requests

Solo prototype, no PRs.

If you ever bring this work to a team setting, the PR description template would include:
- What changed and why
- Testing performed
- Any open questions
- Links to relevant docs

## Tags and releases

Optional but nice: at hour 10, tag the build complete state.

```
git tag -a v0.1-prototype -m "Initial prototype build, 10-hour budget"
git push origin v0.1-prototype
```

This gives reviewers a clear "this is the version they built for the interview" marker.

## What good looks like

A reviewer reading your repo should:
1. Land on README, understand the project in 60 seconds
2. See a clean directory tree, no `__pycache__` or `.DS_Store` cruft
3. See a commit history of 10-12 commits, each with a clear message
4. Be able to run the project locally in 3 commands
5. Find documentation in `docs/` that explains the design

If a reviewer hits a "huh, why is this here?" moment, that's a moment of doubt about your judgment. The repo should be a continuous demonstration of taste.

## Final note

The repo itself is part of the deliverable. A messy repo undercuts a clean PRD. Spend the last 30 minutes of hour 10 polishing:
- README scan
- Remove debug code
- Confirm no secrets
- Test fresh clone setup (`git clone <url> /tmp/test && cd /tmp/test && ...`)

If a fresh clone doesn't work in 5 minutes, the repo isn't done.
