"""
Claude Agent — calls Anthropic Opus 4.8 for complex debugging and architecture.

This agent is optimized for deep analysis, root-cause identification,
and producing minimal, correct diffs. Temperature is set to 0.2
for precision and deterministic reasoning.
"""
import re
from typing import Any

from anthropic import Anthropic

from agents.base import BaseAgent
from config import Config
from utils.logger import AgentLogger
from utils.sandbox import write_sandbox_file, copy_to_workspace


class ClaudeAgent(BaseAgent):
    """
    Elite debugging/architecture agent powered by Claude Opus 4.8.
    Temperature 0.2 for precision and correctness.
    """

    def __init__(self):
        super().__init__("claude")
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def execute(self, task: dict, context: dict | None = None) -> dict[str, Any]:
        """
        Execute a complex debugging/architecture task via Claude Opus.

        Args:
            task: {id, description, tags, files}
            context: optional project context

        Returns:
            Structured result with diff, explanation, and files.
        """
        logger = self.get_logger(task["id"])
        logger.info(f"Starting Claude task: {task['description'][:80]}...")

        system_prompt = Config.CLAUDE_SYSTEM_PROMPT
        user_prompt = self._build_prompt(task, context)

        try:
            response = self.client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=4096,
                temperature=Config.CLAUDE_TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_output = response.content[0].text if response.content else ""
            logger.info("Claude Opus response received")

            # Extract diff and files
            diff = self._extract_diff(raw_output)
            files = self._extract_files(raw_output)
            comments = self._extract_explanation(raw_output)

            # Write files to sandbox
            for f in files:
                write_sandbox_file(task["id"], f["filename"], f["content"])
                logger.info(f"Sandboxed file: {f['filename']}")

            dest = copy_to_workspace(task["id"])

            result = {
                "files": files,
                "diff": diff,
                "comments": comments,
                "model_used": Config.CLAUDE_MODEL,
                "success": True,
                "workspace_path": str(dest),
            }
            logger.info("Claude task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Claude execution failed: {e}")
            return {
                "files": [],
                "diff": "",
                "comments": [f"Error: {e}"],
                "model_used": Config.CLAUDE_MODEL,
                "success": False,
                "error": str(e),
            }

    def _build_prompt(self, task: dict, context: dict | None) -> str:
        """Build a detailed debugging/architecture prompt."""
        parts = [
            f"Task: {task['description']}",
            f"Tags: {', '.join(task.get('tags', []))}",
        ]
        if context and context.get("files"):
            parts.append("\nExisting project files:")
            for fname, fcontent in context["files"].items():
                parts.append(f"\n--- {fname} ---\n{fcontent[:3000]}")
        parts.append(
            "\nAnalyze deeply, find root causes, and produce a minimal clean diff. "
            "If you provide fixed files, wrap them in markdown code blocks with the filename. "
            "Also provide a detailed explanation of the root cause and fix."
        )
        return "\n".join(parts)

    def _extract_diff(self, raw: str) -> str:
        """Extract unified diff from response."""
        diffs = []
        for match in re.finditer(r"```diff\n(.*?)```", raw, re.DOTALL):
            diffs.append(match.group(1).strip())
        return "\n\n".join(diffs) if diffs else ""

    def _extract_files(self, raw: str) -> list[dict]:
        """Extract filename-tagged code blocks."""
        files = []
        pattern = r"```(?:\w+\s+)?([^\n`]+)\n(.*?)```"
        for match in re.finditer(pattern, raw, re.DOTALL):
            fname = match.group(1).strip()
            content = match.group(2).strip()
            # Skip diff blocks
            if fname.startswith("diff") or fname.startswith("diff-"):
                continue
            if fname and content:
                files.append({"filename": fname, "content": content})
        return files

    def _extract_explanation(self, raw: str) -> list[str]:
        """Extract non-code explanatory paragraphs."""
        text = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs
