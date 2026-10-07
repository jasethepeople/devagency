# DevAgency

A Python multi-agent CLI for automating software development tasks. A central "Hermes" orchestrator classifies each task and dispatches it to a worker: a Codex agent (OpenAI GPT-4o), a Claude agent (Anthropic), or a local Ollama model swarm. Task history persists to SQLite, and work executes inside a filtered sandbox.

## Features

- **Task router** (`hermes/task_router.py`) — three-tier classification: explicit `#tags` in the description (`#vibe`, `#bug`, `#test`, `#security`, `#audit`, `#simple`…), LLM fallback (`hermes3:latest` via Ollama), then a default to the local swarm.
- **Codex agent** (`agents/codex_agent.py`) — creative coding/prototyping via OpenAI GPT-4o.
- **Claude agent** (`agents/claude_agent.py`) — debugging and architecture via Anthropic.
- **Local swarm** (`agents/local_swarm.py`) — Ollama model router over a local model inventory (deepseek-coder-v2, granite-code, llama3, target-analyst, auditor, hermes3, …) with an optional `--review` pass by `auditor-8b`.
- **Safety sandbox** (`utils/sandbox.py`) — blocks dangerous patterns (`rm -rf /`, `sudo`, `mkfs`, raw `dd`, dangerous permission changes); writes land in `/tmp/devagency_sandbox/<task_id>/` before promotion to the workspace.
- **Linear integration** (`hermes/linear_client.py`) — GraphQL client for Linear issue lifecycle.
- **Persistence** (`hermes/db.py`) — SQLite task history with UTC timestamps.
- **CLI** (`hermes/main.py`, Click + Rich): `task`, `list`, `status`, `vibes` (mpv lo-fi background music toggle).
- **Logging** (`utils/logger.py`) — Rich console + JSONL output.

## Tech stack

- Python 3.10+, Click, Rich, Pydantic, python-dotenv, requests.
- AI APIs: `openai`, `anthropic` (optional); `ollama` for the local swarm (requires `ollama serve`).
- Optional: mpv (lo-fi music), openai-whisper/sounddevice/numpy (voice input, commented out).
- License: MIT (`LICENSE`).

## Getting started

```bash
git clone https://github.com/jasethepeople/devagency.git
cd devagency
chmod +x setup.sh && ./setup.sh   # creates venv, installs requirements
source venv/bin/activate
cp .env.example .env              # OPENAI_API_KEY, ANTHROPIC_API_KEY, LINEAR_API_KEY, ...
ollama serve                      # in another terminal, for local models
python -m hermes.main --help
```

Usage:

```bash
python -m hermes.main task "Build a React dashboard with dark mode #vibe"
python -m hermes.main task "Fix race condition in worker pool #bug --review" --files app.py,config.py
python -m hermes.main list --status done
python -m hermes.main status <task_id>
python -m hermes.main vibes on
```

## Project structure

```
devagency/
├── README.md / CONTRIBUTING.md / LICENSE
├── requirements.txt / setup.sh / .env.example / config.py
├── hermes/      # main.py (CLI), task_router.py, db.py (SQLite), linear_client.py
├── agents/      # base.py, codex_agent.py, claude_agent.py, local_swarm.py
├── utils/       # sandbox.py, logger.py
├── vibes/       # lofi.py (mpv background music)
└── docs/ARCHITECTURE.md
```

## Status

**Working prototype.** The code is complete and internally consistent (CLI commands, router tiers, sandbox filters, and Linear client all match the README's existing documentation), but it requires live API keys and a local Ollama instance to run; the README's performance claims (e.g. "up to 80% cost reduction") are not verified. The existing README was kept but condensed to the facts the code supports.
