"""
models/operational_rule.py

Pydantic models for data the database schema already expects but
that didn't have a corresponding typed model yet: operational rules
(Phase 6 output) and interview transcripts (Phase 2 output).
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator

from models.heuristic import HeuristicCondition


class OperationalRule(BaseModel):
    """A codified, validated rule derived from an accepted Heuristic.

    Produced by CodificationAgent once a Heuristic's ValidationResult
    decision is "Accepted". This is what MentorAgent searches against.
    """

    rule_id: str = Field(..., description="Unique identifier, e.g. 'RULE001'.")
    heuristic_id: str = Field(..., description="Heuristic this rule was codified from.")
    machine_id: str = Field(..., description="Machine this rule applies to.")
    component: str = Field(..., description="Component involved.")
    failure_type: str = Field(..., description="Failure type this rule predicts.")
    trigger: str = Field(..., description="Human-readable trigger summary.")
    conditions: List[HeuristicCondition] = Field(
        ..., min_length=1, description="Machine-checkable conditions making up the trigger."
    )
    recommended_action: str = Field(..., description="What a technician should do if this fires.")
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence score carried over from validation."
    )
    created_timestamp: datetime = Field(..., description="When this rule was codified.")

    @field_validator(
        "rule_id", "heuristic_id", "machine_id", "component",
        "failure_type", "trigger", "recommended_action",
    )
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    def duplicate_key(self) -> tuple:
        """Key used for duplicate detection before insertion.

        Two rules are considered duplicates if they share the same
        machine, failure type, trigger text, and condition set.
        """
        condition_key = tuple(
            sorted((c.parameter, c.operator, c.value) for c in self.conditions)
        )
        return (self.machine_id, self.failure_type, self.trigger, condition_key)

    model_config = {
        "json_schema_extra": {
            "example": {
                "rule_id": "RULE001",
                "heuristic_id": "HEU001",
                "machine_id": "MACHINE-A",
                "component": "bearing",
                "failure_type": "bearing_failure",
                "trigger": "Humidity > 80% AND Increasing vibration",
                "conditions": [
                    {"parameter": "humidity_percent", "operator": ">", "value": 80},
                    {"parameter": "vibration_mm_s", "operator": ">", "value": 2.0},
                ],
                "recommended_action": "Replace bearing and clean lubrication system",
                "confidence_score": 0.88,
                "created_timestamp": "2026-07-20T16:00:00",
            }
        }
    }


class InterviewTranscript(BaseModel):
    """A saved interview transcript produced by ElicitationAgent."""

    interview_id: str = Field(..., description="Unique identifier, e.g. 'INT001'.")
    employee_id: str = Field(..., description="Employee who was interviewed.")
    incident_id: str = Field(..., description="Historical incident this interview is grounded in.")
    transcript: str = Field(..., description="Full interview transcript text.")
    timestamp: datetime = Field(..., description="When the interview took place.")

    @field_validator("interview_id", "employee_id", "incident_id", "transcript")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "interview_id": "INT001",
                "employee_id": "EMP001",
                "incident_id": "LOG001",
                "transcript": "Q: What did you notice before the bearing failed?\nA: ...",
                "timestamp": "2026-07-20T15:00:00",
            }
        }
    }