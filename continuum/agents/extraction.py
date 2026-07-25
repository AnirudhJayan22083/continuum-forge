"""
agents/extraction.py

KnowledgeExtractionAgent: converts a free-text interview transcript into
a structured Heuristic — a candidate piece of tacit knowledge, not yet
statistically validated.

This agent does NOT judge whether the extracted heuristic is true. That
is entirely ValidationEngine's job (Phase 4). This agent's only
responsibility is faithfully converting prose into the structured
schema, and failing loudly if it can't.

No conflict-detection logic lives here, per the Phase 3 spec.
"""

import json
import logging
import re
from datetime import datetime
from typing import Union

from models.heuristic import Heuristic, HeuristicCondition
from models.operational_rule import InterviewTranscript
from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """\
You are extracting a structured heuristic from an interview transcript \
with a maintenance technician, in order to capture and later validate \
their tacit knowledge.

Given the transcript, output ONLY a single JSON object (no markdown code \
fences, no extra commentary before or after it) with exactly these fields:

{
  "component": "<string>",
  "failure_type": "<string>",
  "trigger": "<human-readable summary of the trigger condition>",
  "conditions": [
    {"parameter": "<string>", "operator": "<one of > >= < <= == !=>", "value": <number>}
  ],
  "symptoms": ["<string>", ...],
  "recommended_action": "<string>",
  "expert_confidence": <number between 0 and 1>
}

Base every field strictly on what the technician actually said. Do not \
invent conditions, thresholds, or numbers that were not mentioned or \
clearly implied in the transcript."""


class ExtractionError(Exception):
    """Raised when a transcript could not be turned into a valid Heuristic.

    Deliberately not swallowed/defaulted anywhere — a failed extraction
    should surface clearly rather than silently producing a fabricated
    or partially-fake heuristic.
    """


class KnowledgeExtractionAgent:
    """Extracts structured Heuristic objects from InterviewTranscript records."""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize the agent.

        Args:
            claude_client: Any ClaudeClient implementation (real or mock).
        """
        self._claude = claude_client

    def extract_heuristic(
        self,
        transcript: InterviewTranscript,
        heuristic_id: str,
        machine_id: str,
        extraction_timestamp: Union[str, datetime],
    ) -> Heuristic:
        """Extract a structured Heuristic from a transcript.

        Args:
            transcript: The interview transcript to extract from.
            heuristic_id: Unique ID to assign to the resulting Heuristic.
            machine_id: Machine this heuristic applies to. Supplied by the
                caller (from the incident the interview was grounded in)
                rather than asked of Claude, since it's already known with
                certainty and shouldn't be re-derived from prose.
            extraction_timestamp: When this extraction is being performed.

        Returns:
            A validated Heuristic instance.

        Raises:
            ExtractionError: if Claude's response isn't valid JSON, or
                doesn't satisfy the Heuristic schema (e.g. confidence out
                of range, missing conditions).
        """
        response = self._claude.generate(EXTRACTION_SYSTEM_PROMPT, transcript.transcript)
        payload = self._parse_json_response(response)

        try:
            conditions = [
                HeuristicCondition(**condition) for condition in payload["conditions"]
            ]
            heuristic = Heuristic(
                heuristic_id=heuristic_id,
                machine_id=machine_id,
                component=payload["component"],
                failure_type=payload["failure_type"],
                trigger=payload["trigger"],
                conditions=conditions,
                symptoms=payload.get("symptoms", []),
                recommended_action=payload["recommended_action"],
                expert_confidence=payload["expert_confidence"],
                extracted_from_interview=transcript.interview_id,
                extraction_timestamp=extraction_timestamp,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ExtractionError(
                f"Extracted JSON did not match the Heuristic schema: {exc}\n"
                f"Raw response was: {response!r}"
            ) from exc

        logger.info(
            "Extracted heuristic %s from interview %s (confidence=%.2f)",
            heuristic.heuristic_id, transcript.interview_id, heuristic.expert_confidence,
        )
        return heuristic

    @staticmethod
    def _parse_json_response(response: str) -> dict:
        """Parse Claude's response as JSON, tolerating markdown code fences.

        Raises:
            ExtractionError: if the response isn't parseable JSON at all.
        """
        cleaned = response.strip()

        fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"Could not parse Claude's response as JSON: {exc}\n"
                f"Raw response was: {response!r}"
            ) from exc