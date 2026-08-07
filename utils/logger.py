"""
Structured logging for DevAgency.

Provides both Rich console output for CLI interaction and JSONL file
logging for audit trails and post-hoc analysis.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

# Shared console for rich output
console = Console()


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get a structured logger with both console (rich) and optional file output.

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to write JSONL logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Rich console handler
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_path=False,
        show_time=False,
    )
    rich_handler.setLevel(logging.INFO)
    rich_format = logging.Formatter("%(message)s")
    rich_handler.setFormatter(rich_format)
    logger.addHandler(rich_handler)

    # File handler (JSONL) if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


class AgentLogger:
    """Per-agent logger that also writes to a shared task log."""

    def __init__(self, agent_name: str, task_id: str):
        self.agent_name = agent_name
        self.task_id = task_id
        self.logger = get_logger(f"devagency.{agent_name}")
        self._entries: list[dict] = []

    def info(self, msg: str) -> None:
        self.logger.info(f"[{self.agent_name}] {msg}")
        self._entries.append({
            "ts": datetime.utcnow().isoformat(),
            "level": "INFO",
            "agent": self.agent_name,
            "task_id": self.task_id,
            "msg": msg,
        })

    def debug(self, msg: str) -> None:
        self.logger.debug(f"[{self.agent_name}] {msg}")
        self._entries.append({
            "ts": datetime.utcnow().isoformat(),
            "level": "DEBUG",
            "agent": self.agent_name,
            "task_id": self.task_id,
            "msg": msg,
        })

    def warning(self, msg: str) -> None:
        self.logger.warning(f"[{self.agent_name}] {msg}")
        self._entries.append({
            "ts": datetime.utcnow().isoformat(),
            "level": "WARNING",
            "agent": self.agent_name,
            "task_id": self.task_id,
            "msg": msg,
        })

    def error(self, msg: str) -> None:
        self.logger.error(f"[{self.agent_name}] {msg}")
        self._entries.append({
            "ts": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "agent": self.agent_name,
            "task_id": self.task_id,
            "msg": msg,
        })

    def get_entries(self) -> list[dict]:
        """Return all log entries for this task."""
        return self._entries.copy()
