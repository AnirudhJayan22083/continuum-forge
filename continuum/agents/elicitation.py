"""
agents/elicitation.py

ElicitationAgent: conducts a grounded interview with a technician about
a specific historical maintenance incident, using Claude to generate
targeted questions and intelligent follow-ups, then saves the resulting
transcript.

No statistical/validation logic lives here — this agent's only job is
producing a good transcript. Whether the resulting claims hold up is
entirely ValidationEngine's job (Phase 4).
"""

import logging
import re
from typing import Callable, List, Tuple

from database.sqlite import Database
from models.employee import Employee
from models.maintenance import MaintenanceLog
from models.operational_rule import InterviewTranscript
from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)

GROUNDED_QUESTIONS_SYSTEM_PROMPT = """\
You are conducting a grounded interview with an experienced maintenance \
technician about a specific historical incident, in order to capture \
their tacit knowledge before they retire. Ask targeted, concrete, \
open-ended interview questions that reference the specific details of \
this incident (machine, component, failure type, description) rather \
than generic questions.

Respond with a numbered list of exactly 3 questions and nothing else."""

FOLLOWUP_QUESTIONS_SYSTEM_PROMPT = """\
You are conducting a follow-up round of a grounded technician interview. \
Given the technician's previous answers, ask intelligent follow-up \
questions that dig into specifics they mentioned: exact thresholds, their \
confidence level, and any conditions where their claim might NOT hold.

Respond with a numbered list of at most 2 questions and nothing else."""


class ElicitationAgent:
    """Conducts grounded interviews and produces InterviewTranscript records."""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize the agent.

        Args:
            claude_client: Any ClaudeClient implementation (real or mock).
                Business logic here never depends on which one it is.
        """
        self._claude = claude_client

    def generate_grounded_questions(
        self, incident: MaintenanceLog, employee: Employee
    ) -> List[str]:
        """Generate interview questions grounded in a specific incident.

        Args:
            incident: The historical maintenance event to ground the interview in.
            employee: The technician being interviewed.

        Returns:
            A list of question strings.
        """
        user_prompt = (
            f"Technician: {employee.name} ({employee.years_experience} years experience)\n"
            f"Machine: {incident.machine_id}\n"
            f"Component: {incident.component}\n"
            f"Failure type: {incident.failure_type}\n"
            f"Description: {incident.description}\n"
            f"Resolution: {incident.resolution}\n"
        )
        response = self._claude.generate(GROUNDED_QUESTIONS_SYSTEM_PROMPT, user_prompt)
        questions = self._parse_numbered_list(response)
        logger.info("Generated %d grounded questions for incident %s", len(questions), incident.log_id)
        return questions

    def generate_followup_questions(
        self, incident: MaintenanceLog, qa_pairs: List[Tuple[str, str]]
    ) -> List[str]:
        """Generate intelligent follow-up questions based on prior answers.

        Args:
            incident: The incident this interview is grounded in.
            qa_pairs: (question, answer) pairs collected so far.

        Returns:
            A list of follow-up question strings (may be empty).
        """
        transcript_so_far = self._format_qa_pairs(qa_pairs)
        user_prompt = (
            f"Incident: {incident.failure_type} on {incident.machine_id} ({incident.component})\n\n"
            f"Interview so far:\n{transcript_so_far}"
        )
        response = self._claude.generate(FOLLOWUP_QUESTIONS_SYSTEM_PROMPT, user_prompt)
        followups = self._parse_numbered_list(response)
        logger.info("Generated %d follow-up questions for incident %s", len(followups), incident.log_id)
        return followups

    def conduct_interview(
        self,
        interview_id: str,
        incident: MaintenanceLog,
        employee: Employee,
        get_answer: Callable[[str], str],
        timestamp: str,
        include_followups: bool = True,
    ) -> InterviewTranscript:
        """Run a full grounded interview (initial questions + follow-ups).

        Args:
            interview_id: Unique ID for this interview, e.g. 'INT004'.
            incident: The historical incident this interview is grounded in.
            employee: The technician being interviewed.
            get_answer: Callback that returns an answer string for a given
                question. In production this would be wired to the real
                technician's responses (e.g. via an MCP client turn); in
                tests/demos it can be backed by scripted or mock answers.
            timestamp: ISO timestamp to record for this interview.
            include_followups: Whether to run a follow-up round after the
                initial questions.

        Returns:
            The completed InterviewTranscript.
        """
        qa_pairs: List[Tuple[str, str]] = []

        for question in self.generate_grounded_questions(incident, employee):
            answer = get_answer(question)
            qa_pairs.append((question, answer))

        if include_followups:
            for question in self.generate_followup_questions(incident, qa_pairs):
                answer = get_answer(question)
                qa_pairs.append((question, answer))

        transcript_text = self._format_qa_pairs(qa_pairs)

        transcript = InterviewTranscript(
            interview_id=interview_id,
            employee_id=employee.employee_id,
            incident_id=incident.log_id,
            transcript=transcript_text,
            timestamp=timestamp,
        )
        logger.info(
            "Completed interview %s with %s (%d Q&A pairs)",
            interview_id, employee.employee_id, len(qa_pairs),
        )
        return transcript

    def save_transcript(self, transcript: InterviewTranscript, db: Database) -> None:
        """Persist a completed InterviewTranscript to the database.

        Args:
            transcript: The transcript to save.
            db: An already-connected Database instance.
        """
        db.insert_interview_transcript(transcript)
        logger.info("Saved transcript %s to database", transcript.interview_id)

    @staticmethod
    def _format_qa_pairs(qa_pairs: List[Tuple[str, str]]) -> str:
        """Format (question, answer) pairs into transcript text."""
        lines = []
        for question, answer in qa_pairs:
            lines.append(f"Q: {question}")
            lines.append(f"A: {answer}")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def _parse_numbered_list(text: str) -> List[str]:
        """Parse a numbered list ('1. ...', '2. ...') into clean strings.

        Falls back to treating each non-blank line as its own item if no
        numbering is detected, so this stays robust to minor formatting
        variance from either the real or mock Claude client.
        """
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            items.append(match.group(1).strip() if match else line)
        return items