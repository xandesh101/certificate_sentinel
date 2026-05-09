# 07 Security Checklist

> Security requirements for this prototype. None of these are optional. The cost of getting any of them wrong is real (leaked credentials, runaway API spend, embarrassment in interview review).

## Credentials and secrets

- [ ] `ANTHROPIC_API_KEY` is read from environment variable only. Never hardcoded.
- [ ] `APP_PASSWORD` is read from environment variable only. Never hardcoded.
- [ ] `.env` file is in `.gitignore` and confirmed not tracked: run `git status` and verify `.env` does not appear.
- [ ] `.env.example` is committed and contains placeholder values only (e.g., `ANTHROPIC_API_KEY=sk-ant-...`)
- [ ] No secrets appear in committed files. Run `git log -p | grep -i "sk-ant"` before pushing to confirm.
- [ ] On Streamlit Cloud, secrets are added via the Settings -> Secrets UI, not in the code.
- [ ] If a key is ever accidentally committed: rotate it immediately in the Anthropic Console, then `git filter-branch` or use BFG Repo-Cleaner to scrub history.

## API spending controls

- [ ] Spending limit set on Anthropic account: $20 USD.
- [ ] Per-session API call cap in the app: a session counter increments on each validation; if it exceeds 20, show a "session limit reached" message.
- [ ] Eval harness has a "confirm before running" prompt in the UI ("This will cost approximately $0.50; continue?").
- [ ] Logs do not include API responses with sensitive data (none in this prototype, since data is synthetic, but the practice matters).

## Application access

- [ ] Streamlit Cloud app is gated by password using `st.text_input(type="password")`.
- [ ] Password is compared using `hmac.compare_digest()` (not `==`, which is timing-vulnerable).
- [ ] Failed password attempts produce a generic error ("Invalid password"), not specifying whether the password was wrong vs another error.
- [ ] After login, `st.session_state.authenticated = True` is set; every page checks this before rendering.
- [ ] No "remember me" cookies or persistent sessions; password is re-required on browser refresh.

## Data handling

- [ ] All data is synthetic. No real customer names, taxpayer IDs, or transaction data anywhere.
- [ ] A persistent banner at the top of the UI states "Prototype. Synthetic data only. Do not enter real customer or transaction data."
- [ ] User-uploaded files (if upload is enabled in any future iteration) are processed in memory and not persisted to disk.
- [ ] Logs (`logs/runs.jsonl`, `logs/overrides.jsonl`) are in `.gitignore`. They contain run history that could expose prompt details, but no real PII.

## Dependency hygiene

- [ ] `requirements.txt` pins all major dependencies to a tested version range (e.g., `anthropic>=0.40.0,<1.0.0`).
- [ ] Run `pip list --outdated` before deploying; review any major-version differences.
- [ ] No dependencies pulled from arbitrary git repos or unofficial sources.
- [ ] No installation of `langchain`, `llama-index`, or other heavy frameworks (per the architectural decision).

## Code-level security practices

- [ ] No `eval()` or `exec()` anywhere in the codebase.
- [ ] All file I/O uses `pathlib.Path`, never string concatenation that could allow path traversal.
- [ ] Mock data file paths are constants, not user-controlled inputs.
- [ ] JSON parsing wrapped in try/except for `json.JSONDecodeError`.
- [ ] No bare `except:` clauses; always catch specific exceptions.
- [ ] Type hints on all public functions; this is a security signal as much as a quality one (well-typed code is easier to audit).

## Logging and observability

- [ ] Logs do not contain the API key, password, or any secret value.
- [ ] Log files use append-mode (`a`), not write-mode, to prevent accidental truncation.
- [ ] Log rotation is not implemented for the prototype; if the file exceeds 100MB, manually truncate. (Production would use `logging.handlers.RotatingFileHandler`.)
- [ ] Streamlit's debug mode is OFF in deployment. Confirm `streamlit run --server.runOnSave false` and no debug widgets visible.

## Rate limiting

- [ ] Per-session validation cap: 20 runs.
- [ ] Per-session eval cap: 1 full eval run (10 scenarios).
- [ ] If Anthropic rate limit error occurs (`anthropic.RateLimitError`): catch, show user-facing message ("API is rate-limited; wait 30 seconds"), do not retry indefinitely.

## Repository hygiene

- [ ] Repository is private until explicitly shared with reviewers via a link.
- [ ] No commit messages reference internal Vertex info, real customer names, or anything that wouldn't pass a public-repo sanity check.
- [ ] `.git/` is not deployed to Streamlit Cloud (Streamlit auto-pulls from GitHub; the `.git/` dir is irrelevant on the server).
- [ ] Any test fixtures with realistic-looking data have a clear "synthetic test data" comment.

## What this prototype does NOT need (but production would)

These are deliberately out of scope for the prototype. If asked in the interview, the answer is "this is a prototype; production would add..."

- SOC 2 controls
- SAML/SSO integration
- Encryption at rest for logs
- Data residency controls
- Audit log retention policies
- GDPR/CCPA data handling flows
- Penetration testing
- Dependency vulnerability scanning (e.g., Snyk, Dependabot)
- API key rotation automation
- Vulnerability disclosure program

Calling these out in the interview signals you know what production looks like. Including them in the prototype would balloon scope.

## Pre-deployment final check

Run through this list before clicking "Deploy" on Streamlit Cloud:

1. `git status` shows clean working tree
2. `cat .gitignore` includes `.env`, `logs/`, `data/certificates/*.pdf`, `__pycache__`, `.venv`
3. `grep -r "sk-ant" .` returns nothing (other than `.env.example` placeholder)
4. `grep -r "APP_PASSWORD" src/` shows only env-var reads, no hardcoded values
5. Spending limit confirmed in Anthropic Console
6. Password gate tested locally
7. Smoke test on at least one PASS and one FLAG scenario locally before pushing
