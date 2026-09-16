"""Loads and renders the per-state system prompts in /prompts.

Each state has its own narrowly-scoped prompt file. This module's only job
is to inject patient context into the right template — it does not call
any LLM.
"""

from __future__ import annotations

from pathlib import Path

from app.patient_record import PatientRecord
from app.state_machine import ConversationState

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_STATE_FILENAMES: dict[ConversationState, str] = {
    ConversationState.GREETING: "greeting.txt",
    ConversationState.VERIFY_IDENTITY: "verify_identity.txt",
    ConversationState.MEDICATION_CHECK: "medication_check.txt",
    ConversationState.SIDE_EFFECT_CHECK: "side_effect_check.txt",
    ConversationState.ESCALATION_CHECK: "escalation_check.txt",
    ConversationState.CLOSING: "closing.txt",
}

CARE_TEAM_NAME = "Riverside General Post-Discharge Care Team"


def _build_context(patient: PatientRecord) -> dict[str, str]:
    medications_block = "\n".join(
        f"  - {med.name} {med.dosage}, {med.frequency}" for med in patient.medications
    )
    allergies = ", ".join(patient.allergies) if patient.allergies else "None on file"
    red_flags = ", ".join(patient.red_flag_symptoms)

    return {
        "care_team_name": CARE_TEAM_NAME,
        "patient_name": patient.name,
        "discharge_diagnosis": patient.discharge_diagnosis,
        "allergies": allergies,
        "medications_block": medications_block,
        "red_flags": red_flags,
        "follow_up_date": patient.follow_up_date.isoformat(),
    }


def render_prompt(state: ConversationState, patient: PatientRecord) -> str:
    """Return the fully rendered system prompt for the given state."""
    filename = _STATE_FILENAMES[state]
    template = (PROMPTS_DIR / filename).read_text()
    context = _build_context(patient)
    return template.format(**context)
