"""
models/maintenance.py

Pydantic models for historical maintenance events and sensor readings —
the ground-truth data that heuristics get statistically validated against.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MaintenanceLog(BaseModel):
    """A single historical maintenance/failure event for a machine."""

    log_id: str = Field(..., description="Unique identifier, e.g. 'LOG001'.")
    machine_id: str = Field(..., description="Machine this event occurred on.")
    component: str = Field(..., description="Component involved, e.g. 'bearing'.")
    failure_type: str = Field(
        ..., description="Type of failure/event, e.g. 'bearing_failure'."
    )
    timestamp: datetime = Field(..., description="When the event occurred.")
    description: str = Field(..., description="Free-text description of the event.")
    technician_id: str = Field(
        ..., description="Employee ID of the technician who handled it."
    )
    resolution: str = Field(..., description="How the issue was resolved.")

    @field_validator("log_id", "machine_id", "component", "failure_type", "technician_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "log_id": "LOG001",
                "machine_id": "MACHINE-A",
                "component": "bearing",
                "failure_type": "bearing_failure",
                "timestamp": "2026-07-20T14:30:00",
                "description": "Bearing overheated due to high humidity and vibration",
                "technician_id": "EMP001",
                "resolution": "Replaced bearing, cleaned lubrication system",
            }
        }
    }


class SensorReading(BaseModel):
    """A single historical (or live) sensor reading for a machine.

    Used both to build the historical dataset that heuristics are
    validated against, and as the input to the MentorAgent for live
    recommendations.
    """

    reading_id: str = Field(..., description="Unique identifier, e.g. 'SENSOR001'.")
    machine_id: str = Field(..., description="Machine this reading came from.")
    timestamp: datetime = Field(..., description="When the reading was taken.")
    humidity_percent: float = Field(..., ge=0, le=100, description="Relative humidity, 0-100.")
    vibration_mm_s: float = Field(..., ge=0, description="Vibration velocity in mm/s.")
    temperature_celsius: float = Field(..., description="Temperature in degrees Celsius.")
    pressure_bar: float = Field(..., ge=0, description="Pressure in bar.")

    @field_validator("reading_id", "machine_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "reading_id": "SENSOR001",
                "machine_id": "MACHINE-A",
                "timestamp": "2026-07-20T14:00:00",
                "humidity_percent": 85.5,
                "vibration_mm_s": 2.3,
                "temperature_celsius": 72.1,
                "pressure_bar": 6.2,
            }
        }
    }