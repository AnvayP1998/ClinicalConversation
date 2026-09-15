"""Synthetic patient record data model.

All data validated by this model is entirely fictional and used only for
demonstration purposes. See SPEC.md for the project's non-goals.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class Medication(BaseModel):
    name: str = Field(min_length=1)
    dosage: str = Field(min_length=1)
    frequency: str = Field(min_length=1)


class PatientRecord(BaseModel):
    patient_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    discharge_diagnosis: str = Field(min_length=1)
    medications: list[Medication] = Field(min_length=1)
    allergies: list[str]
    red_flag_symptoms: list[str] = Field(min_length=1)
    follow_up_date: date

    @field_validator("medications")
    @classmethod
    def medications_not_empty(cls, v: list[Medication]) -> list[Medication]:
        if not v:
            raise ValueError("medications must contain at least one entry")
        return v

    @field_validator("red_flag_symptoms")
    @classmethod
    def red_flags_not_empty(cls, v: list[str]) -> list[str]:
        if not v or any(not s.strip() for s in v):
            raise ValueError("red_flag_symptoms must contain at least one non-empty entry")
        return v
