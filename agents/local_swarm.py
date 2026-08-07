"""
Local Agent Swarm — Ollama model router with chain-of-thought review pipeline.

Manages a pool of local Ollama models, routing tasks to the optimal
model based on intent tags. Supports a two-stage chain-of-thought
review pipeline where a secondary model audits generated output.
"""
import re
from typing import Any

import ollama

from agents.base import BaseAgent
from config import Config
from utils.logger import AgentLogger
from utils.sandbox import write_sandbox_file, copy_to_workspace


class LocalOrchestrator(BaseAgent):
    """
    Manages a swarm of local Ollama models.
    Routes tasks to the optimal model based on tags/intent.
    Supports chain-of-thought review pipeline (--review flag).
    """

    def __init__(self):
        super().__init__("local_swarm")
        self.host = Config.OLLAMA_HOST
        # Verify Ollama connection
        try:
            ollama.list()
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Ollama at {self.host}: {e}")

    def execute(self, task: dict, context: dict | None = None) -> dict[str, Any]:
        """
        Execute a task using the local model swarm.

        Args:
            task: {id, description, tags, files, review (bool)}
            context: optional project context

        Returns:
            Structured result with generated files, comments, and model chain.
        """
        logger = self.get_logger(task["id"])
        tags = task.get("tags", [])
        review = task.get("review", False)

        # Select primary model
        primary, fallback = self._select_models(tags)
        logger.info(f"Selected models: primary={primary}, fallback={fallback}")

        # Build prompt
        prompt = self._build_prompt(task, context)

        # Run primary model
        raw_output = self._run_model(primary, fallback, prompt, logger)
        if not raw_output:
            return {
                "files": [],
                "comments": ["Local model produced no output"],
                "model_used": primary,
                "success": False,
            }

        # Extract files and comments
        files = self._extract_files(raw_output)
        comments = self._extract_comments(raw_output)

        # Chain-of-thought review pipeline
        if review and files:
            logger.info("Running review pipeline...")
            reviewed = self._review_pipeline(task, files, primary, logger)
            files = reviewed["files"]
            comments.extend(reviewed["comments"])

        # Write to sandbox
        for f in files:
            write_sandbox_file(task["id"], f["filename"], f["content"])
            logger.info(f"Sandboxed file: {f['filename']}")

        # Copy to workspace
        dest = copy_to_workspace(task["id"])

        return {
            "files": files,
            "comments": comments,
            "model_used": primary,
            "review_model": "auditor-8b:latest" if review else None,
            "success": True,
            "workspace_path": str(dest),
        }

    def _select_models(self, tags: list[str]) -> tuple[str, str]:
        """
        Select primary and fallback models based on task tags.

        Args:
            tags: List of hashtag strings (e.g., ['#test', '#simple'])

        Returns:
            (primary_model, fallback_model)
        """
        clean_tags = [t.lstrip("#").lower() for t in tags]

        for tag in clean_tags:
            if tag in Config.LOCAL_MODEL_MAP:
                mapping = Config.LOCAL_MODEL_MAP[tag]
                return mapping["primary"], mapping["fallback"]

        # Default to general
        mapping = Config.LOCAL_MODEL_MAP["general"]
        return mapping["primary"], mapping["fallback"]

    def _build_prompt(self, task: dict, context: dict | None) -> str:
        """Build a detailed prompt for the local model."""
        parts = [
            "You are a helpful coding assistant. Generate clean, working code.",
            f"\nTask: {task['description']}",
            f"Tags: {', '.join(task.get('tags', []))}",
        ]
        if context and context.get("files"):
            parts.append("\nExisting project files:")
            for fname, fcontent in context["files"].items():
                parts.append(f"\n--- {fname} ---\n{fcontent[:2000]}")
        parts.append(
            "\nOutput each file in a markdown code block with the filename as the language tag, e.g.:",
        )
        parts.append("```python filename.py\n# code here\n```")
        return "\n".join(parts)

    def _run_model(
        self,
        primary: str,
        fallback: str,
        prompt: str,
        logger: AgentLogger,
    ) -> str:
        """
        Run a model via Ollama with fallback.

        Args:
            primary: Primary model name
            fallback: Fallback model name
            prompt: Full prompt text
            logger: Agent logger

        Returns:
            Model output string
        """
        for model in [primary, fallback]:
            try:
                logger.info(f"Calling Ollama model: {model}")
                response = ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.3},
                )
                output = response["message"]["content"]
                logger.info(f"Model {model} responded ({len(output)} chars)")
                return output
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        logger.error("All local models failed")
        return ""

    def _review_pipeline(
        self,
        task: dict,
        files: list[dict],
        generator_model: str,
        logger: AgentLogger,
    ) -> dict[str, Any]:
        """
        Chain-of-thought review: auditor reviews generated files.

        Args:
            task: Original task dict
            files: Generated files from primary model
            generator_model: Name of the model that generated the files
            logger: Agent logger

        Returns:
            dict with reviewed files and review comments
        """
        reviewer = "auditor-8b:latest"
        review_comments = []
        reviewed_files = []

        for f in files:
            review_prompt = (
                f"Review this code for bugs, security issues, and code smells.\n"
                f"File: {f['filename']}\n"
                f"Generated by: {generator_model}\n\n"
                f"```\n{f['content']}\n```\n\n"
                f"Provide a corrected version if needed, or confirm it is good."
            )
            try:
                response = ollama.chat(
                    model=reviewer,
                    messages=[{"role": "user", "content": review_prompt}],
                    options={"temperature": 0.1},
                )
                review_output = response["message"]["content"]
                review_comments.append(f"Review of {f['filename']}: {review_output[:500]}")

                # Try to extract corrected file from review
                corrected = self._extract_files(review_output)
                if corrected:
                    reviewed_files.extend(corrected)
                else:
                    reviewed_files.append(f)
            except Exception as e:
                logger.warning(f"Review failed for {f['filename']}: {e}")
                reviewed_files.append(f)

        return {"files": reviewed_files, "comments": review_comments}

    def _extract_files(self, raw: str) -> list[dict]:
        """Extract filename-tagged code blocks from markdown."""
        files = []
        pattern = r"```(?:\w+\s+)?([^\n`]+)\n(.*?)```"
        for match in re.finditer(pattern, raw, re.DOTALL):
            fname = match.group(1).strip()
            content = match.group(2).strip()
            if fname and content and not fname.startswith("diff"):
                files.append({"filename": fname, "content": content})
        return files

    def _extract_comments(self, raw: str) -> list[str]:
        """Extract non-code explanatory text."""
        text = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines
