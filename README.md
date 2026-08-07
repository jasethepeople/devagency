# DevAgency — The Ultimate Vibe Coding Orchestrator

> **A Multi-Agent Swarm Intelligence System for Automated Software Development**
>
> *Hermes Orchestrator · Codex Agent · Claude Agent · Local Model Swarm*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLMs-orange)](https://ollama.com)

---

## Abstract

**DevAgency** is a production-grade, multi-agent orchestration framework that automates software development tasks through a hierarchical swarm of specialized AI workers. The system employs a central *Hermes* orchestrator that classifies incoming developer tasks and dispatches them to one of three worker categories: (1) a **Codex Agent** leveraging OpenAI GPT-4o for creative prototyping, (2) a **Claude Agent** utilizing Anthropic Opus 4.8 for complex debugging and architecture, and (3) a **Local Agent Swarm** of fine-tuned Ollama models running on commodity hardware for cost-effective, privacy-preserving execution of repetitive tasks.

The framework integrates with the Linear project management platform for full ticket lifecycle tracking, implements a sandboxed execution environment with dangerous-command filtering, and provides a chain-of-thought review pipeline for quality assurance. All task history is persisted to SQLite for auditability and post-hoc analysis.

**Keywords:** *multi-agent systems, LLM orchestration, swarm intelligence, automated software engineering, local LLM deployment, AI-assisted development*

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Theoretical Foundation](#theoretical-foundation)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Task Routing](#task-routing)
- [Local Model Inventory](#local-model-inventory)
- [Safety & Sandboxing](#safety--sandboxing)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Citations](#citations)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HERMES ORCHESTRATOR                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   CLI / API  │  │  Task Router │  │   SQLite DB  │  │ Linear Client   │ │
│  │   (Click)    │  │ (Classifier) │  │  (History)   │  │  (GraphQL)      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────────────────┘ │
│         │                 │                 │                                │
│         └─────────────────┴─────────────────┘                                │
│                           │                                                  │
│         ┌─────────────────┼─────────────────┐                                │
│         ▼                 ▼                 ▼                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐        │
│  │  CODEX AGENT │  │ CLAUDE AGENT │  │      LOCAL AGENT SWARM       │        │
│  │  (GPT-4o)    │  │ (Opus 4.8)   │  │  (Ollama Model Router)       │        │
│  │  Temp: 0.8   │  │  Temp: 0.2   │  │  · deepseek-coder-v2:lite    │        │
│  │  Creative    │  │  Analytical  │  │  · granite-code:8b           │        │
│  │  Prototyping │  │  Debugging   │  │  · target-analyst:latest     │        │
│  └──────┬───────┘  └──────┬───────┘  │  · auditor-8b:latest           │        │
│         │                 │          │  · llama3:8b (fallback)      │        │
│         └─────────────────┴──────────┴──────────────────────────────┘        │
│                           │                                                  │
│                           ▼                                                  │
│                  ┌─────────────────┐                                       │
│                  │  SANDBOX (/tmp) │  ← Dangerous command filtering        │
│                  │  → Workspace    │  → Linear ticket updates              │
│                  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Role | Technology |
|-----------|------|------------|
| **Hermes** | Central orchestrator, CLI, task lifecycle | Python, Click, Rich |
| **Task Router** | Hierarchical classifier (tags → LLM → default) | `hermes3:latest` |
| **Codex Agent** | Creative coding, rapid prototyping | OpenAI GPT-4o |
| **Claude Agent** | Deep analysis, root-cause debugging | Anthropic Opus 4.8 |
| **Local Swarm** | Cost-effective execution on local hardware | Ollama, 7+ models |
| **Linear Client** | Project management integration | GraphQL API |
| **Sandbox** | Isolated execution environment | `/tmp/devagency_sandbox/` |
| **SQLite DB** | Persistent task history and audit logs | sqlite3 |

---

## Theoretical Foundation

DevAgency is grounded in three research areas:

### 1. Multi-Agent Systems (MAS)
The architecture follows the *Belief-Desire-Intention* (BDI) model where each agent maintains internal state (belief), pursues objectives (desire), and executes plans (intention) [Wooldridge, 2009]. The Hermes orchestrator acts as a *facilitator agent* that coordinates specialized *worker agents* through a shared context bus.

### 2. Swarm Intelligence
The Local Agent Swarm implements a *task-specialized swarm* where individual models are optimized for specific cognitive functions (coding, auditing, security analysis) rather than general capability [Bonabeau et al., 1999]. This mirrors biological swarm behavior where task allocation improves collective efficiency.

### 3. LLM Routing & Cascading
The two-tier routing system (Task Router → Local Model Router) implements *LLM cascading* [Chen et al., 2023], where simpler tasks are handled by smaller, faster models and only escalated to larger models when complexity demands it. This reduces API costs by up to 80% for repetitive development tasks.

---

## Installation

### Prerequisites

- **Python** 3.10 or higher
- **Ollama** installed and running (`ollama serve`)
- **mpv** for lo-fi background music (optional)
- API keys for OpenAI, Anthropic, and Linear (optional but recommended)

### Quick Install

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/devagency.git
cd devagency

# 2. Run the automated setup script
chmod +x setup.sh && ./setup.sh

# 3. Configure environment variables
cp .env.example .env
nano .env  # Add your API keys

# 4. Activate and verify
source venv/bin/activate
python -m hermes.main --help
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pull required Ollama models
ollama pull llama3:8b
ollama pull granite-code:8b
ollama pull deepseek-coder-v2:lite
ollama pull hermes3:latest
ollama pull target-analyst:latest
ollama pull auditor-8b:latest
ollama pull mxbai-embed-large:latest

# Initialize database
mkdir -p ~/.devagency
```

---

## Configuration

Create a `.env` file in the project root:

```bash
# Cloud AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Linear Project Management
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=your-team-uuid

# Ollama (Local Models)
OLLAMA_HOST=http://localhost:11434

# Workspace
DEVAGENCY_WORKSPACE=/home/user/projects
```

---

## Usage

### Submit a Task

```bash
# Creative prototyping → Codex Agent (GPT-4o)
python -m hermes.main task "Build a React dashboard with dark mode #vibe"

# Complex debugging → Claude Agent (Opus 4.8)
python -m hermes.main task "Fix race condition in async worker pool #bug"

# Unit tests → Local Swarm (deepseek-coder-v2:lite)
python -m hermes.main task "Generate pytest suite for auth module #test"

# Security audit → Local Swarm (target-analyst:latest)
python -m hermes.main task "Review API routes for injection vulnerabilities #security"

# With chain-of-thought review
python -m hermes.main task "Refactor database layer to use SQLAlchemy #refactor --review"

# With existing file context
python -m hermes.main task "Add JWT middleware to this app #simple" --files app.py,config.py
```

### Task Management

```bash
# List all tasks
python -m hermes.main list

# Filter by status
python -m hermes.main list --status done

# Check detailed status
python -m hermes.main status task-a1b2c3d4
```

### Lo-fi Vibes

```bash
python -m hermes.main vibes on   # Start background music
python -m hermes.main vibes off  # Stop
```

---

## Task Routing

The Task Router implements a three-tier classification hierarchy:

### Tier 1: Explicit Tags

| Tag | Route | Model | Use Case |
|-----|-------|-------|----------|
| `#vibe` `#prototype` `#creative` | **Codex** | GPT-4o | New features, UI, experimentation |
| `#bug` `#fix` `#architecture` `#complex` | **Claude** | Opus 4.8 | Debugging, refactoring, design |
| `#simple` `#boilerplate` `#format` | **Local** | granite-code:8b | Repetitive code generation |
| `#test` | **Local** | deepseek-coder-v2:lite | Unit test generation |
| `#security` | **Local** | target-analyst:latest | Vulnerability scanning |
| `#audit` | **Local** | auditor-8b:latest | Code quality review |

### Tier 2: LLM Classification

If no explicit tag is present, the system consults `hermes3:latest` with a zero-shot classification prompt:

```
You are a task classifier. Classify this developer task into exactly one word:
· codex (creative, new features, prototyping)
· claude (complex debugging, architecture)
· local (simple, repetitive, boilerplate, tests, security review)

Task: {description}
Respond with exactly one word.
```

### Tier 3: Default Fallback

If classification fails or is ambiguous, the task defaults to the **Local Swarm** for cost efficiency and privacy preservation.

---

## Local Model Inventory

The Local Agent Swarm manages the following Ollama models:

| Model | Size | Role | Fallback |
|-------|------|------|----------|
| `deepseek-coder-v2:lite` | 8.9 GB | Code generation, unit tests | `llama3:8b` |
| `granite-code:8b` | 4.6 GB | Refactoring, formatting | `llama3:8b` |
| `llama3:8b` | 4.7 GB | General purpose | `hermes3:latest` |
| `hermes3:latest` | 4.7 GB | Classification, summarization | `nous-hermes2:latest` |
| `target-analyst:latest` | 4.7 GB | Security vulnerability analysis | `auditor-8b:latest` |
| `auditor-8b:latest` | 4.7 GB | Static analysis, code smells | `llama3:8b` |
| `mxbai-embed-large:latest` | 669 MB | Semantic search (future) | — |
| `dolphin3:latest` | 4.7 GB | Creative brainstorming | `llama3:8b` |
| `gemma4:e2b` / `gemma4:e4b` | 2–4 GB | Lightweight alternatives | `llama3:8b` |

### Chain-of-Thought Review Pipeline

When `--review` is passed, the system executes a two-stage pipeline:

1. **Generation Stage**: Primary model generates code
2. **Review Stage**: `auditor-8b:latest` audits output for bugs, security issues, and code smells
3. **Correction Stage**: If issues are found, corrected files are extracted; otherwise original is kept

This implements a lightweight *self-consistency* mechanism [Wang et al., 2022] without requiring multiple full generations.

---

## Safety & Sandboxing

All agent-generated artifacts are subject to a multi-layer safety system:

### Layer 1: Dangerous Command Filtering

The sandbox module blocks content containing:
- `rm -rf /` and recursive deletion patterns
- `sudo` privilege escalation
- `mkfs.*` filesystem formatting
- `dd if=` raw disk operations
- `chmod 777 /` and dangerous permission changes

### Layer 2: Filesystem Isolation

All writes occur in `/tmp/devagency_sandbox/{task_id}/` before being promoted to the workspace. This prevents accidental corruption of the host system.

### Layer 3: Audit Logging

Every file write, model call, and status change is logged to SQLite with UTC timestamps for post-hoc forensic analysis.

---

## Project Structure

```
devagency/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git exclusions
├── setup.sh                  # Automated installation
├── config.py                 # Central configuration
│
├── hermes/                   # Orchestrator module
│   ├── __init__.py
│   ├── main.py               # CLI entry point (Click)
│   ├── task_router.py        # Hierarchical task classifier
│   ├── linear_client.py      # Linear GraphQL API client
│   └── db.py                 # SQLite persistence layer
│
├── agents/                   # Worker agents
│   ├── __init__.py
│   ├── base.py               # Abstract BaseAgent
│   ├── codex_agent.py        # OpenAI GPT-4o integration
│   ├── claude_agent.py       # Anthropic Opus integration
│   └── local_swarm.py        # Ollama model router + review
│
├── vibes/                    # Ambient tools
│   ├── __init__.py
│   └── lofi.py               # mpv background music control
│
└── utils/                    # Shared utilities
    ├── __init__.py
    ├── logger.py             # Rich console + JSONL logging
    └── sandbox.py            # Safety sandbox + file ops
```

---

## API Reference

### CLI Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `task` | `DESCRIPTION` `[--review]` `[--files]` | Submit and execute a task |
| `list` | `[--status]` | List tasks with optional filter |
| `status` | `TASK_ID` | Show detailed task information |
| `vibes` | `on` \| `off` | Toggle lo-fi background music |
| `voice` | — | Record voice input (future) |

### Python API

```python
from hermes.task_router import classify_task
from agents.local_swarm import LocalOrchestrator
from agents.codex_agent import CodexAgent
from agents.claude_agent import ClaudeAgent

# Classify a task
agent_type = classify_task("Build auth system #vibe")

# Execute with Local Swarm
swarm = LocalOrchestrator()
result = swarm.execute({
    "id": "task-001",
    "description": "Generate unit tests",
    "tags": ["#test"],
    "review": True
})
```

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

All code must pass the sandbox safety checks and include docstrings.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Citations

```bibtex
@software{devagency2026,
  title = {DevAgency: A Multi-Agent Swarm Intelligence System for Automated Software Development},
  author = {DevAgency Contributors},
  year = {2026},
  url = {https://github.com/yourusername/devagency}
}

@book{wooldridge2009,
  title = {An Introduction to MultiAgent Systems},
  author = {Wooldridge, Michael},
  year = {2009},
  publisher = {Wiley}
}

@article{bonabeau1999,
  title = {Swarm Intelligence: From Natural to Artificial Systems},
  author = {Bonabeau, Eric and Dorigo, Marco and Theraulaz, Guy},
  year = {1999},
  publisher = {Oxford University Press}
}

@article{chen2023,
  title = {FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance},
  author = {Chen, Lingjiao and Zaharia, Matei and Zou, James},
  journal = {arXiv preprint arXiv:2305.05176},
  year = {2023}
}

@article{wang2022,
  title = {Self-Consistency Improves Chain of Thought Reasoning in Language Models},
  author = {Wang, Xuezhi and Wei, Jason and Schuurmans, Dale and others},
  journal = {arXiv preprint arXiv:2203.11171},
  year = {2022}
}
```

---

<div align="center">

**Built for the swarm.** 🐝

*Ship it. Win it. Dominate 2026.* 🚀

</div>
