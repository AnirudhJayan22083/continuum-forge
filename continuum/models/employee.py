"""
models/employee.py

Pydantic model for a technician/employee whose tacit knowledge
Continuum is trying to capture before they retire.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class Employee(BaseModel):
    """A technician with domain expertise on a specific machine.

    Used to build the interview queue (ordered by experience, then
    retirement date) and to attribute interview transcripts and
    maintenance log entries to a specific person.
    """

    employee_id: str = Field(..., description="Unique identifier, e.g. 'EMP001'.")
    name: str = Field(..., description="Full name of the technician.")
    machine_id: str = Field(
        ..., description="Machine this technician is primarily expert on, e.g. 'MACHINE-A'."
    )
    years_experience: int = Field(
        ..., ge=0, description="Years of hands-on experience with this machine."
    )
    retirement_date: datetime = Field(
        ..., description="Planned or expected retirement date."
    )
    expertise_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas of expertise, e.g. ['bearing maintenance', 'vibration analysis'].",
    )
    interview_completed: bool = Field(
        default=False, description="Whether this technician has completed their interview."
    )

    @field_validator("employee_id", "name", "machine_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "employee_id": "EMP001",
                "name": "John Smith",
                "machine_id": "MACHINE-A",
                "years_experience": 25,
                "retirement_date": "2026-12-31T00:00:00",
                "expertise_areas": ["bearing maintenance", "vibration analysis"],
                "interview_completed": False,
            }
        }
    }