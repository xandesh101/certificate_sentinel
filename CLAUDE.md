# CLAUDE.md

> Project context for Claude Code. Read this first.

## What this project is

**Certificate Sentinel** is a 10-hour prototype of an agentic AI system that performs semantic validation of sales tax exemption certificates. It is built as a Principal PM interview deliverable for Vertex Inc, demonstrating responsible AI design, evaluation discipline, and human-in-the-loop architecture.

This is a prototype, not a production system. The point is to demonstrate Principal-level thinking through the artifact, not to ship.

## Project goals (in priority order)

1. The agent works correctly on the 10 eval scenarios in `docs/06_TEST_SCENARIOS.md`
2. The eval harness runs all scenarios and reports precision, recall, calibration, latency
3. The Streamlit UI lets a non-technical reviewer interact with the prototype
4. The code is clean enough that a reviewer can read it in 30 minutes
5. The deployment is live on Streamlit Cloud with a password gate

## Hard constraints

- **Do not use LangChain, LlamaIndex, or any agent framework.** Use Anthropic's native tool use directly. This is a deliberate design choice for inspectability.
- **Do not hard-code the Anthropic API key.** Always read from environment variable `ANTHROPIC_API_KEY`.
- **Do not commit `.env`, `logs/`, `data/certificates/*.pdf`, or any secret.** The `.gitignore` template covers these.
- **Do not put real customer data anywhere.** Synthetic data only. Every UI must banner this.
- **Do not skip the post-decision verifier.** The agent's cited rule_ids must be validated against the rules table after every decision. This is the defense-in-depth pattern that makes this prototype Principal-grade.
- **Do not exceed 10 tool-use rounds in the agent loop.** Hard cap.
- **Do not call the API without retries.** Use exponential backoff for transient errors.

## Tech stack (locked)

- Python 3.11
- Streamlit (latest stable)
- `anthropic` Python SDK (latest)
- `pydantic` for schemas
- `pytest` for eval
- `python-dotenv` for env loading
- `reportlab` for synthetic PDF generation (or `weasyprint` if simpler)

Do not introduce dependencies outside this list without flagging in the chat first.

## Project structure (target)

```
certificate-sentinel/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── streamlit_app.py
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── tools.py
│   │   ├── prompts.py
│   │   └── verifier.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── store.py
│   ├── eval/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── metrics.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── pages.py
│   │   └── components.py
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── auth.py
├── data/
│   ├── customers.json
│   ├── transactions.json
│   ├── rules.json
│   └── certificates/
├── eval_scenarios/
│   └── scenarios.json
├── tests/
│   ├── test_tools.py
│   ├── test_agent.py
│   └── test_eval.py
├── logs/
│   └── .gitkeep
└── docs/   (this package, copied in)
```

## Coding conventions

- Type hints on all public functions
- Docstrings on all modules and classes (Google style)
- Use `pydantic` models for any structured data crossing module boundaries
- One responsibility per module; if a file passes 300 lines, refactor
- No global state outside of `src/data/store.py` (which loads JSON once at import time)
- Logging: use Python's `logging` module, configure once in `src/utils/logging.py`, never `print` in production code paths
- Error handling: catch specific exceptions, never bare `except`
- File I/O: use `pathlib.Path`, never string paths

## Build sequence

Follow `docs/03_IMPLEMENTATION_GUIDE.md` hour by hour. Do not skip ahead. Each hour ends with a working state and a commit.

## Commit conventions

- One commit per build hour, with a clear message
- Format: `[hour-N] short description`
- Examples: `[hour-1] initial repo setup`, `[hour-5] agent orchestrator with tool use loop`
- Use conventional-commit style for the body if helpful

## What "done" means for each component

| Component | Done when |
| --- | --- |
| Mock data | All JSON files validated against schemas in `docs/05_DATA_SPECIFICATIONS.md` |
| Tools | Each tool has a unit test that asserts return shape and one happy path |
| Agent | Runs end-to-end on at least 3 scenarios, produces structured output |
| Verifier | Catches a hand-crafted hallucinated rule_id case |
| UI | Loads in browser, scenario picker works, results render |
| Eval | Runs all 10 scenarios, produces a metrics report |
| Deployment | Live URL responds, password gate works, smoke test passes |

## What NOT to build

- No real OCR
- No real Vertex API calls
- No multi-state reasoning beyond Texas
- No model fine-tuning
- No fancy CSS or theming
- No more than 10 eval scenarios
- No streaming responses
- No multi-turn conversation (each validation is a fresh agent loop)
- No user authentication beyond the single password gate
- No production-grade observability (local JSONL logs only)

If you find yourself building any of the above, stop. The prototype is for demonstrating design discipline, not feature richness.

## When in doubt

Ask the human (in chat). Do not guess on:
- Architecture decisions not specified here
- Data schemas not in `docs/05_DATA_SPECIFICATIONS.md`
- Eval thresholds not in the PRD
- Whether to add a dependency

When the implementation guide is unambiguous, just execute.
