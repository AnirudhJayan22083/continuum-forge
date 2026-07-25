"""
utils/claude_client.py

Abstraction over "ask Claude something" so agents (ElicitationAgent now,
KnowledgeExtractionAgent in Phase 3) can depend on a ClaudeClient
interface without caring whether it's backed by the real Anthropic API
or a deterministic mock. Business logic in agents/ never imports
`anthropic` directly — only this module does.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"


class ClaudeClient(ABC):
    """Interface for generating text from a prompt via Claude."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Generate a response given a system prompt and a user prompt.

        Args:
            system_prompt: Instructions describing the task/role.
            user_prompt: The actual content/question to respond to.
            max_tokens: Maximum tokens in the response.

        Returns:
            The generated text response.
        """
        raise NotImplementedError


class RealClaudeClient(ClaudeClient):
    """ClaudeClient backed by the real Anthropic API.

    Requires the `anthropic` package and an ANTHROPIC_API_KEY environment
    variable (or an explicit api_key passed to the constructor).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "RealClaudeClient requires an API key: pass api_key= explicitly "
                "or set the ANTHROPIC_API_KEY environment variable."
            )

        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for RealClaudeClient. "
                "Install it with: pip install anthropic"
            ) from exc

        self._client = anthropic.Anthropic(api_key=resolved_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        logger.debug("Calling Claude API (model=%s)", self.model)
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_blocks = [block.text for block in response.content if block.type == "text"]
        return "\n".join(text_blocks).strip()


class MockClaudeClient(ClaudeClient):
    """Deterministic ClaudeClient for local development, tests, and demos
    that shouldn't depend on a live API key or network access.

    Responses are chosen based on keywords in the system prompt, so
    callers get plausible, differentiated output for grounded questions
    vs. follow-up questions vs. other future uses (e.g. Phase 3
    extraction) without any real model call.
    """

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        prompt_lower = system_prompt.lower()

        if "extract" in prompt_lower and "heuristic" in prompt_lower:
            return (
                "{\n"
                '  "component": "bearing",\n'
                '  "failure_type": "bearing_failure",\n'
                '  "trigger": "Humidity > 80% AND Increasing vibration",\n'
                '  "conditions": [\n'
                '    {"parameter": "humidity_percent", "operator": ">", "value": 80},\n'
                '    {"parameter": "vibration_mm_s", "operator": ">", "value": 2.0}\n'
                "  ],\n"
                '  "symptoms": ["overheating", "noise", "vibration"],\n'
                '  "recommended_action": "Replace bearing and clean lubrication system",\n'
                '  "expert_confidence": 0.9\n'
                "}"
            )

        if "follow-up" in prompt_lower or "followup" in prompt_lower:
            return (
                "1. You mentioned a specific threshold — is there an exact value where "
                "you'd consider the risk urgent versus just worth monitoring?\n"
                "2. Are there any conditions where this pattern does NOT hold, that "
                "a newer technician should watch out for?"
            )

        if "grounded" in prompt_lower or "interview questions" in prompt_lower:
            return (
                "1. Walk me through exactly what you observed right before this incident.\n"
                "2. What readings or signs made you confident about what was happening?\n"
                "3. What would you tell a newer technician to watch for in a similar situation?"
            )

        # Generic fallback for any other future prompt type. Logged loudly
        # rather than silently, since reaching this branch usually means a
        # system prompt was reworded and no longer matches any known keyword
        # above — better to notice that immediately than get a shorter,
        # wrong-shaped response with no explanation.
        logger.warning(
            "MockClaudeClient: system prompt matched no known category, "
            "using generic fallback. First 80 chars: %r",
            system_prompt[:80],
        )
        return (
            "1. Can you describe what happened in more detail?\n"
            "2. What made you confident in your assessment?"
        )