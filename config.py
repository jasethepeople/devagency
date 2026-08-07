"""
DevAgency Configuration — loads environment variables and defines
model routing constants for the multi-agent orchestration system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_dotenv_path = Path(__file__).parent / ".env"
if _dotenv_path.exists():
    load_dotenv(_dotenv_path)
else:
    load_dotenv()


class Config:
    """Central configuration singleton for the DevAgency orchestrator."""

    # ── API Keys ──────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LINEAR_API_KEY: str = os.getenv("LINEAR_API_KEY", "")
    LINEAR_TEAM_ID: str = os.getenv("LINEAR_TEAM_ID", "")

    # ── Ollama ────────────────────────────────────────
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # ── Workspace ─────────────────────────────────────
    DEVAGENCY_WORKSPACE: Path = Path(
        os.getenv("DEVAGENCY_WORKSPACE", str(Path.home() / "projects"))
    )

    # ── Database ──────────────────────────────────────
    DB_PATH: Path = Path.home() / ".devagency" / "hermes.db"

    # ── Sandbox ───────────────────────────────────────
    SANDBOX_DIR: Path = Path("/tmp/devagency_sandbox")

    # ── Vibes ───────────────────────────────────────
    LOFI_URL: str = "https://www.youtube.com/watch?v=jfKfPfyJRdk"

    # ── Local Model Router Mapping ────────────────────
    # Maps task intent tags to optimal Ollama models with fallbacks.
    # See README.md for model descriptions and hardware requirements.
    LOCAL_MODEL_MAP: dict[str, dict[str, str]] = {
        "boilerplate": {"primary": "granite-code:8b", "fallback": "llama3:8b"},
        "format":      {"primary": "granite-code:8b", "fallback": "llama3:8b"},
        "simple":      {"primary": "granite-code:8b", "fallback": "llama3:8b"},
        "test":        {"primary": "deepseek-coder-v2:lite", "fallback": "llama3:8b"},
        "security":    {"primary": "target-analyst:latest", "fallback": "auditor-8b:latest"},
        "audit":       {"primary": "auditor-8b:latest", "fallback": "llama3:8b"},
        "refactor":    {"primary": "deepseek-coder-v2:lite", "fallback": "granite-code:8b"},
        "general":     {"primary": "llama3:8b", "fallback": "hermes3:latest"},
    }

    # Model used for untagged task classification
    CLASSIFIER_MODEL: str = "hermes3:latest"

    # ── Cloud Model Configuration ─────────────────────
    CODEX_MODEL: str = "gpt-4o"
    CODEX_TEMPERATURE: float = 0.8
    CODEX_SYSTEM_PROMPT: str = (
        "You are a creative, vibe-driven coder. Generate complete, working code "
        "based on the user's idea. Embrace experimentation. Output clean, runnable code."
    )

    CLAUDE_MODEL: str = "claude-opus-4-8-20250219"
    CLAUDE_TEMPERATURE: float = 0.2
    CLAUDE_SYSTEM_PROMPT: str = (
        "You are an elite software engineer. Analyze the problem deeply, find root causes, "
        "and produce a minimal, clean diff. Prioritize correctness and safety. "
        "Return a unified diff and detailed explanation."
    )

    @classmethod
    def ensure_dirs(cls) -> None:
        """Ensure all required runtime directories exist."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        cls.DEVAGENCY_WORKSPACE.mkdir(parents=True, exist_ok=True)
