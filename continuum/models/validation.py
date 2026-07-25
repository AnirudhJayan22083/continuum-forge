"""
models/validation.py

Pydantic model for the output of the ValidationEngine — the strongly
typed, statistically-grounded verdict on a Heuristic.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ValidationResult(BaseModel):
    """Statistical validation outcome for a single Heuristic.

    Produced entirely by the ValidationEngine (Pandas/NumPy/SciPy) —
    no LLM involvement. This is the object that determines whether a
    heuristic becomes operational knowledge or gets rejected.
    """

    validation_id: str = Field(..., description="Unique identifier, e.g. 'VAL001'.")
    heuristic_id: str = Field(..., description="ID of the Heuristic being validated.")

    support_count: int = Field(
        ..., ge=0, description="Number of historical occurrences matching the trigger."
    )
    total_occurrences: int = Field(
        ..., ge=0, description="Total number of historical events considered."
    )
    conditional_probability: float = Field(
        ..., ge=0, le=1, description="P(failure | trigger conditions met)."
    )
    pearson_correlation: float = Field(
        ..., ge=-1, le=1, description="Pearson correlation between trigger and failure."
    )
    chi_square_statistic: float = Field(
        ..., ge=0, description="Chi-square test statistic."
    )
    chi_square_p_value: float = Field(
        ..., ge=0, le=1, description="p-value from the chi-square test."
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Overall computed confidence score for this heuristic."
    )
    decision: Literal["Accepted", "Rejected"] = Field(
        ..., description="Final decision based on the statistical evidence."
    )
    reasoning: str = Field(
        ..., description="Human-readable explanation of why this decision was reached."
    )
    validation_timestamp: datetime = Field(
        ..., description="When this validation was performed."
    )

    @field_validator("validation_id", "heuristic_id", "reasoning")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def support_cannot_exceed_total(self) -> "ValidationResult":
        if self.support_count > self.total_occurrences:
            raise ValueError("support_count cannot exceed total_occurrences")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "validation_id": "VAL001",
                "heuristic_id": "HEU001",
                "support_count": 32,
                "total_occurrences": 92,
                "conditional_probability": 0.85,
                "pearson_correlation": 0.78,
                "chi_square_statistic": 24.5,
                "chi_square_p_value": 0.0001,
                "confidence_score": 0.88,
                "decision": "Accepted",
                "reasoning": "Strong statistical support with p-value < 0.05",
                "validation_timestamp": "2026-07-20T15:30:00",
            }
        }
    }