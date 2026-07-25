"""
models/heuristic.py

Pydantic models for a heuristic extracted from an interview transcript —
a candidate piece of tacit knowledge, not yet statistically validated.
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class HeuristicCondition(BaseModel):
    """A single machine-checkable condition within a heuristic's trigger.

    e.g. {"parameter": "humidity_percent", "operator": ">", "value": 80}
    """

    parameter: str = Field(..., description="Sensor/log field this condition applies to.")
    operator: Literal[">", ">=", "<", "<=", "==", "!="] = Field(
        ..., description="Comparison operator."
    )
    value: float = Field(..., description="Threshold value being compared against.")

    @field_validator("parameter")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value


class Heuristic(BaseModel):
    """A structured, candidate piece of tacit knowledge extracted from
    an interview transcript, prior to statistical validation.
    """

    heuristic_id: str = Field(..., description="Unique identifier, e.g. 'HEU001'.")
    machine_id: str = Field(..., description="Machine this heuristic applies to.")
    component: str = Field(..., description="Component involved, e.g. 'bearing'.")
    failure_type: str = Field(..., description="Failure type this heuristic predicts.")
    trigger: str = Field(
        ..., description="Human-readable trigger summary, e.g. 'Humidity > 80% AND Increasing vibration'."
    )
    conditions: List[HeuristicCondition] = Field(
        ..., min_length=1, description="Machine-checkable conditions making up the trigger."
    )
    symptoms: List[str] = Field(
        default_factory=list, description="Observable symptoms, e.g. ['overheating', 'noise']."
    )
    recommended_action: str = Field(..., description="What a technician should do if this fires.")
    expert_confidence: float = Field(
        ..., ge=0, le=1, description="Technician's stated confidence in this heuristic, 0-1."
    )
    extracted_from_interview: str = Field(
        ..., description="Interview transcript ID this heuristic was extracted from."
    )
    extraction_timestamp: datetime = Field(
        ..., description="When this heuristic was extracted."
    )

    @field_validator(
        "heuristic_id", "machine_id", "component", "failure_type",
        "trigger", "recommended_action", "extracted_from_interview",
    )
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "heuristic_id": "HEU001",
                "machine_id": "MACHINE-A",
                "component": "bearing",
                "failure_type": "bearing_failure",
                "trigger": "Humidity > 80% AND Increasing vibration",
                "conditions": [
                    {"parameter": "humidity_percent", "operator": ">", "value": 80},
                    {"parameter": "vibration_mm_s", "operator": ">", "value": 2.0},
                ],
                "symptoms": ["overheating", "noise", "vibration"],
                "recommended_action": "Replace bearing and clean lubrication system",
                "expert_confidence": 0.95,
                "extracted_from_interview": "INT001",
                "extraction_timestamp": "2026-07-20T15:00:00",
            }
        }
    }