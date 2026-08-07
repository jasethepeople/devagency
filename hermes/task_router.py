"""
Task Router — classifies developer tasks and routes to the correct agent category.

Implements a hierarchical classification system:
  1. Explicit hashtag tags in the task description
  2. Fallback to a lightweight local LLM classifier (hermes3)
  3. Default to local swarm for safety
"""
import re
from typing import Literal

import ollama

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Tag-to-agent mapping
TAG_ROUTES = {
    "codex": {"#vibe", "#prototype", "#idea", "#creative"},
    "claude": {"#bug", "#fix", "#refactor", "#architecture", "#complex"},
    "local": {"#simple", "#test", "#boilerplate", "#format", "#security", "#audit"},
}


def extract_tags(description: str) -> list[str]:
    """Extract all #tags from a description string."""
    return re.findall(r"#\w+", description)


def classify_task(description: str) -> Literal["codex", "claude", "local"]:
    """
    Classify a developer task into one of three agent categories.

    Priority:
      1. Explicit tags in description
      2. Fallback to hermes3:latest classifier
      3. Default to "local"

    Args:
        description: Raw task description string

    Returns:
        One of: "codex", "claude", "local"
    """
    tags = extract_tags(description)
    clean_tags = {t.lower() for t in tags}

    # 1. Check explicit tags
    for agent, tag_set in TAG_ROUTES.items():
        if clean_tags & tag_set:
            logger.info(f"Routed by tag to {agent}: {clean_tags & tag_set}")
            return agent  # type: ignore[return-value]

    # 2. Fallback: ask hermes3 to classify
    try:
        logger.info("No explicit tags found. Consulting hermes3 classifier...")
        prompt = (
            "You are a task classifier. Classify this developer task into exactly one word:\n"
            "· codex (creative, new features, prototyping)\n"
            "· claude (complex debugging, architecture)\n"
            "· local (simple, repetitive, boilerplate, tests, security review)\n\n"
            f"Task: {description}\n"
            "Respond with exactly one word: codex, claude, or local."
        )
        response = ollama.chat(
            model=Config.CLASSIFIER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
        )
        classification = response["message"]["content"].strip().lower()

        # Validate response
        if classification in ("codex", "claude", "local"):
            logger.info(f"Hermes3 classified as: {classification}")
            return classification  # type: ignore[return-value]
        else:
            logger.warning(f"Invalid classifier response: {classification}. Defaulting to local.")

    except Exception as e:
        logger.warning(f"Classifier failed: {e}. Defaulting to local.")

    # 3. Default
    logger.info("Default route: local")
    return "local"
