# Architecture Deep Dive

## Design Principles

1. **Separation of Concerns**: Each agent handles one cognitive function
2. **Fail-Safe Defaults**: Untagged tasks route to local (cheapest/safest)
3. **Observability**: Every decision is logged and auditable
4. **Extensibility**: New agents and models plug in via BaseAgent

## Data Flow

```
User Input
    │
    ▼
┌─────────────┐
│   Parser    │  → Extract tags, build task dict
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Task Router  │  → Tier 1: tags | Tier 2: LLM | Tier 3: default
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Agent      │  → Execute with context + sandbox
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Sandbox    │  → Safety check → Write to /tmp
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Promote    │  → Copy to workspace
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Linear     │  → Update ticket status
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SQLite     │  → Persist result + logs
└─────────────┘
```

## Model Selection Heuristics

The Local Model Router uses a deterministic lookup table based on task intent. This is preferred over dynamic routing because:

- **Determinism**: Same task always routes to same model (reproducible)
- **Transparency**: Routing decisions are inspectable in config.py
- **Efficiency**: No additional LLM call required for routing

Future work may explore learned routing policies via reinforcement learning.

## Security Model

DevAgency operates on a **deny-by-default** principle:

- All generated code is sandboxed before execution
- Dangerous patterns are blocked via regex (not AST parsing, for speed)
- API keys are never logged or exposed in task output
- Local models run entirely on-device (no data leaves the machine)
