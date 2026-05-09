# 08 Deployment Guide

> Step-by-step deployment to Streamlit Cloud. Roughly 30 minutes the first time, 5 minutes for redeploys.

## Prerequisites

- GitHub repo for the project, pushed to `main`
- Streamlit Cloud account (free, sign in with GitHub at https://share.streamlit.io)
- Anthropic API key
- Chosen `APP_PASSWORD` for the password gate

## First-time deployment

### Step 1: Connect Streamlit Cloud to your repo

1. Sign in to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository
4. Branch: `main`
5. Main file path: `streamlit_app.py`
6. App URL: choose a generic slug (e.g., `cert-validator-prototype.streamlit.app`). Do NOT use anything containing "vertex".
7. Click "Advanced settings" before deploying.

### Step 2: Add secrets

In the Advanced settings:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-...your-actual-key..."
APP_PASSWORD = "your-chosen-password"
```

Format is TOML. Double-quotes around values. No surrounding curly braces.

### Step 3: Deploy

Click "Deploy". The first deployment takes 2-5 minutes:
- Streamlit Cloud clones your repo
- Installs from `requirements.txt`
- Starts your app

If deployment fails, click "Manage app" -> "Logs" and look for the error. Common issues:

| Error | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` | Dependency missing from `requirements.txt` | Add it, push, redeploy |
| `KeyError: 'ANTHROPIC_API_KEY'` | Secret name typo or missing | Check Settings -> Secrets |
| `streamlit.errors.StreamlitAPIException` | App crashed on first render | Run locally first; fix; push |
| App spins forever | Out of memory (rare) or import-time hang | Check that `src/data/store.py` doesn't make API calls at import |

### Step 4: Smoke test

Open the deployed URL. You should see:
1. Password prompt
2. After entering password, the validation page
3. The synthetic data banner at the top
4. The scenario picker showing 10 scenarios

Run scenario C_001. It should complete in 15-30 seconds and show a PASS decision with green banner.

If it fails, check:
- Are the certificate PDFs in the repo? (They're in `.gitignore` for the binary copies; the `scripts/generate_certificates.py` should run at deploy time, OR you commit the PDFs explicitly. For Streamlit Cloud, commit the PDFs.)
- Is the API key correct?
- Is the password correct?

### Step 5: Set spending limit

If you haven't already:
1. Anthropic Console -> Settings -> Billing -> Spending limit
2. Set to $20 USD
3. Confirm the alert email is set to your address

## Redeployment after code changes

Streamlit Cloud watches the GitHub repo. Every push to `main` triggers a redeploy automatically (takes 1-2 minutes). No manual action needed.

To force a redeploy without code changes: Manage app -> Reboot.

## Pre-interview pre-warming

Streamlit Cloud apps sleep after periods of inactivity. First request after sleep takes 30-60 seconds.

Before any interview where you might share the URL:
1. Open the URL in your browser
2. Enter password
3. Confirm the page loads
4. Run scenario C_001 to wake any cached state

Do this 10 minutes before the interview. The app stays warm for at least an hour after activity.

## Sharing the URL

When you share the URL with the hiring team:

```
Live demo: https://cert-validator-prototype.streamlit.app
Password: [provide separately, e.g. in interview chat or in followup email]
Note: This is a prototype with synthetic data only. The first load may take ~30 seconds 
to wake the server. If you see anything unexpected, the GitHub repo includes a Loom 
walkthrough video.
```

Send the password in a separate channel from the URL. This is overkill for a prototype but signals security thinking.

## Monitoring during interview week

Bookmark:
- The deployed app URL
- The Streamlit Cloud management page (for logs)
- The Anthropic Console usage page (to watch spending)

Check the Anthropic Console after the interview. If usage is unexpectedly high, check the Streamlit Cloud logs to see if someone hit the URL repeatedly.

## Tearing it down

After the interview process is complete:

1. Streamlit Cloud: Manage app -> Delete app
2. Anthropic Console: rotate the API key (just in case)
3. GitHub: archive the repo (don't delete; you may want to reference it later)
4. Update your `.env` to remove the rotated key

## Alternative deployment paths

If Streamlit Cloud doesn't work for some reason:

**Option B: Hugging Face Spaces**
- Free tier supports Streamlit
- Same workflow: connect GitHub repo, add secrets
- Slight branding difference (HF logo)

**Option C: Local-only with Loom walkthrough**
- If deployment fails entirely, the fallback is a recorded Loom showing the local app
- Honest framing in interview: "Streamlit Cloud deployment is in the README; the demo here is the local version because of [X]; full deployment plan is documented."
- This is acceptable but inferior to a live URL.

**Option D: Render or Railway**
- More setup, more options, more failure modes
- Not recommended for a 10-hour prototype

## What "deployment success" looks like

You will know deployment is good when:
- The URL loads in under 30 seconds (after wake)
- The password gate works
- A friend you DM the URL to can run a scenario successfully
- The Anthropic Console shows the expected API calls
- No errors in Streamlit Cloud logs

That's the bar. Anything beyond is polish you don't need.
