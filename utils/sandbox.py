"""
Sandbox utilities — safe file operations and dangerous-command filtering.

All agent-generated code is written to a temporary sandbox directory
before being promoted to the workspace. This module blocks dangerous
shell commands and filesystem operations.
"""
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Dangerous commands that are blocked in sandbox
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"sudo\s+",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/",
    r"chmod\s+777\s+/",
    r"chown\s+-R\s+root",
    r"\$\(rm\s+-rf",
    r"`rm\s+-rf",
]

DANGEROUS_REGEX = re.compile("|".join(DANGEROUS_PATTERNS), re.IGNORECASE)


def is_dangerous(content: str) -> bool:
    """
    Check if content contains dangerous shell commands.

    Args:
        content: Code or command string to scan

    Returns:
        True if dangerous patterns detected
    """
    return bool(DANGEROUS_REGEX.search(content))


def get_sandbox_path(task_id: str) -> Path:
    """
    Get the sandbox directory for a specific task.

    Args:
        task_id: Unique task identifier

    Returns:
        Path to task sandbox directory
    """
    sandbox = Config.SANDBOX_DIR / task_id
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


def write_sandbox_file(task_id: str, filename: str, content: str) -> Path:
    """
    Write a file to the task sandbox after safety checks.

    Args:
        task_id: Task identifier
        filename: Target filename
        content: File content

    Returns:
        Path to written file

    Raises:
        ValueError: If dangerous commands detected in content
    """
    if is_dangerous(content):
        logger.error(f"Dangerous content detected in {filename} — blocked")
        raise ValueError(f"Dangerous commands detected in {filename}. Operation blocked.")

    sandbox = get_sandbox_path(task_id)
    filepath = sandbox / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Sandboxed: {filepath}")
    return filepath


def copy_to_workspace(task_id: str, target_dir: Optional[Path] = None) -> Path:
    """
    Copy all files from sandbox to the target workspace directory.

    Args:
        task_id: Task identifier
        target_dir: Destination directory (defaults to DEVAGENCY_WORKSPACE / task_id)

    Returns:
        Path to destination directory
    """
    sandbox = get_sandbox_path(task_id)
    dest = target_dir or (Config.DEVAGENCY_WORKSPACE / task_id)
    dest.mkdir(parents=True, exist_ok=True)

    if sandbox.exists():
        for item in sandbox.iterdir():
            if item.is_file():
                shutil.copy2(item, dest / item.name)
            elif item.is_dir():
                shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
        logger.info(f"Copied sandbox -> {dest}")
    else:
        logger.warning(f"Sandbox empty for task {task_id}")

    return dest


def run_in_sandbox(task_id: str, command: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """
    Run a command inside the task sandbox with safety checks.

    Args:
        task_id: Task identifier
        command: Command as list of strings
        timeout: Max seconds to wait

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If dangerous command detected
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    cmd_str = " ".join(command)
    if is_dangerous(cmd_str):
        raise ValueError(f"Dangerous command blocked: {cmd_str}")

    sandbox = get_sandbox_path(task_id)
    logger.info(f"Running in sandbox: {cmd_str}")

    return subprocess.run(
        command,
        cwd=sandbox,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def cleanup_sandbox(task_id: str) -> None:
    """Remove a task's sandbox directory."""
    sandbox = Config.SANDBOX_DIR / task_id
    if sandbox.exists():
        shutil.rmtree(sandbox)
        logger.info(f"Cleaned up sandbox for {task_id}")
