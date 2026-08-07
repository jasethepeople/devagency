"""
Codex Agent — calls OpenAI GPT-4o for creative, vibe-driven coding.

This agent is optimized for rapid prototyping, creative exploration,
and generating complete, working implementations from high-level ideas.
Temperature is set to 0.8 to encourage experimentation.
"""
import re
from typing import Any

from openai import OpenAI

from agents.base import BaseAgent
from config import Config
from utils.logger import AgentLogger
from utils.sandbox import write_sandbox_file, copy_to_workspace


class CodexAgent(BaseAgent):
    """
    Creative coding agent powered by OpenAI GPT-4o.
    Temperature 0.8 for experimentation and vibe coding.
    """

    def __init__(self):
        super().__init__("codex")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def execute(self, task: dict, context: dict | None = None) -> dict[str, Any]:
        """
        Execute a creative coding task via GPT-4o.

        Args:
            task: {id, description, tags, files}
            context: optional project context

        Returns:
            Structured result with generated files and comments.
        """
        logger = self.get_logger(task["id"])
        logger.info(f"Starting Codex task: {task['description'][:80]}...")

        # Build system + user prompt
        system_prompt = Config.CODEX_SYSTEM_PROMPT
        user_prompt = self._build_prompt(task, context)

        try:
            response = self.client.chat.completions.create(
                model=Config.CODEX_MODEL,
                temperature=Config.CODEX_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_output = response.choices[0].message.content or ""
            logger.info("GPT-4o response received")

            # Parse code blocks from markdown
            files = self._extract_files(raw_output)
            comments = self._extract_comments(raw_output)

            # Write to sandbox
            for f in files:
                write_sandbox_file(task["id"], f["filename"], f["content"])
                logger.info(f"Sandboxed file: {f['filename']}")

            # Copy to workspace
            dest = copy_to_workspace(task["id"])

            result = {
                "files": files,
                "comments": comments,
                "model_used": Config.CODEX_MODEL,
                "success": True,
                "workspace_path": str(dest),
            }
            logger.info("Codex task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Codex execution failed: {e}")
            return {
                "files": [],
                "comments": [f"Error: {e}"],
                "model_used": Config.CODEX_MODEL,
                "success": False,
                "error": str(e),
            }

    def _build_prompt(self, task: dict, context: dict | None) -> str:
        """Build a detailed prompt for the creative task."""
        parts = [
            f"Task: {task['description']}",
            f"Tags: {', '.join(task.get('tags', []))}",
        ]
        if context and context.get("files"):
            parts.append("\nExisting project files:")
            for fname, fcontent in context["files"].items():
                parts.append(f"\n--- {fname} ---\n{fcontent[:2000]}")
        parts.append(
            "\nGenerate complete, working code. Wrap each file in markdown code blocks "
            "with the filename as the language tag, e.g.:",
        )
        parts.append("```python filename.py\n# code here\n```")
        return "\n".join(parts)

    def _extract_files(self, raw: str) -> list[dict]:
        """Extract filename-tagged code blocks from markdown."""
        files = []
        pattern = r"```(?:\w+\s+)?([^\n`]+)\n(.*?)```"
        for match in re.finditer(pattern, raw, re.DOTALL):
            fname = match.group(1).strip()
            content = match.group(2).strip()
            if fname and content:
                files.append({"filename": fname, "content": content})
        return files

    def _extract_comments(self, raw: str) -> list[str]:
        """Extract non-code explanatory text."""
        text = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines
