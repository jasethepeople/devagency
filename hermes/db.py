"""
SQLite database for task history and metadata.

Provides persistent storage for all orchestrated tasks, including
status tracking, result serialization, and per-task audit logging.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id              TEXT PRIMARY KEY,
    description     TEXT NOT NULL,
    tags            TEXT,           -- JSON array
    agent           TEXT NOT NULL,  -- codex | claude | local
    model_used      TEXT,           -- specific model name
    linear_issue_id TEXT,
    status          TEXT DEFAULT 'pending',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    completed_at    TEXT,
    result_json     TEXT,           -- JSON result dict
    error           TEXT
);

CREATE TABLE IF NOT EXISTS task_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL REFERENCES tasks(id),
    agent       TEXT NOT NULL,
    level       TEXT NOT NULL,
    message     TEXT NOT NULL,
    timestamp   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_logs_task   ON task_logs(task_id);
"""


class TaskDB:
    """SQLite-backed task history store."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def create_task(
        self,
        task_id: str,
        description: str,
        tags: list[str],
        agent: str,
        linear_issue_id: str = "",
    ) -> None:
        """Insert a new task record."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, description, tags, agent, linear_issue_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, description, ",".join(tags), agent, linear_issue_id, "pending", now, now),
            )
            conn.commit()
        logger.info(f"Task {task_id} recorded in DB")

    def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status and optional result/error."""
        now = datetime.utcnow().isoformat()
        completed = now if status in ("done", "failed") else None
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, updated_at = ?, completed_at = ?, result_json = ?, error = ?
                WHERE id = ?
                """,
                (
                    status,
                    now,
                    completed,
                    json.dumps(result) if result else None,
                    error,
                    task_id,
                ),
            )
            conn.commit()
        logger.info(f"Task {task_id} status -> {status}")

    def log_entry(self, task_id: str, agent: str, level: str, message: str) -> None:
        """Append a log entry for a task."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO task_logs (task_id, agent, level, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (task_id, agent, level, message, now),
            )
            conn.commit()

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Fetch a single task by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        """List tasks with optional status filter."""
        query = "SELECT * FROM tasks"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params += (limit,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_task_logs(self, task_id: str) -> list[dict[str, Any]]:
        """Fetch all logs for a specific task."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM task_logs WHERE task_id = ? ORDER BY timestamp",
                (task_id,),
            ).fetchall()
            return [dict(row) for row in rows]
