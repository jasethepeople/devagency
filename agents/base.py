"""
Abstract base class for all DevAgency agents.

Defines the contract that every agent (Codex, Claude, LocalSwarm)
must implement to participate in the orchestration pipeline.
"""
from abc import ABC, abstractmethod
from typing import Any

from utils.logger import AgentLogger


class BaseAgent(ABC):
    """
    Abstract base for all agents (Codex, Claude, LocalSwarm).

    Every agent must implement:
      - execute(task, context) -> dict with files, comments, model_used
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, task: dict, context: dict | None = None) -> dict[str, Any]:
        """
        Execute a task and return structured results.

        Args:
            task: dict with keys: id, description, tags, files (optional)
            context: optional additional context (project files, history, etc.)

        Returns:
            dict with keys:
                - files: list of {filename, content}
                - comments: list of str (explanations, diffs, notes)
                - model_used: str (which model/agent processed this)
                - success: bool
        """
        ...

    def get_logger(self, task_id: str) -> AgentLogger:
        """Get a logger scoped to this agent and task."""
        return AgentLogger(self.name, task_id)
