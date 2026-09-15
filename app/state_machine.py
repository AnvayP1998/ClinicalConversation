"""Deterministic conversation state machine.

This module contains no LLM calls. In particular, the red-flag escalation
check in `StateMachine.check_for_red_flag` / `handle_patient_message` is
implemented as hard-coded keyword/regex matching against the patient's own
`red_flag_symptoms` list, independent of any AI output. This is the primary
safety mechanism against the "missed escalation" guardrail category
described in SPEC.md: escalation must not depend on an LLM behaving
correctly.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from app.patient_record import PatientRecord


class ConversationState(str, Enum):
    GREETING = "GREETING"
    VERIFY_IDENTITY = "VERIFY_IDENTITY"
    MEDICATION_CHECK = "MEDICATION_CHECK"
    SIDE_EFFECT_CHECK = "SIDE_EFFECT_CHECK"
    ESCALATION_CHECK = "ESCALATION_CHECK"
    CLOSING = "CLOSING"


# Normal linear progression. CLOSING has no successor (terminal state).
_NEXT_STATE: dict[ConversationState, Optional[ConversationState]] = {
    ConversationState.GREETING: ConversationState.VERIFY_IDENTITY,
    ConversationState.VERIFY_IDENTITY: ConversationState.MEDICATION_CHECK,
    ConversationState.MEDICATION_CHECK: ConversationState.SIDE_EFFECT_CHECK,
    ConversationState.SIDE_EFFECT_CHECK: ConversationState.ESCALATION_CHECK,
    ConversationState.ESCALATION_CHECK: ConversationState.CLOSING,
    ConversationState.CLOSING: None,
}


class InvalidTransitionError(Exception):
    """Raised when advancing from a state that has no valid successor."""


class StateMachine:
    def __init__(
        self,
        patient_record: PatientRecord,
        state: ConversationState = ConversationState.GREETING,
    ) -> None:
        self.patient_record = patient_record
        self.state = state
        self.escalated = False
        self._escalation_reason: Optional[str] = None

    def check_for_red_flag(self, patient_text: str) -> Optional[str]:
        """Return the matched red-flag symptom text, or None if no match.

        Matching is plain keyword/substring matching (case-insensitive,
        word-boundary aware) against the patient's own red_flag_symptoms
        list. This does not call any LLM and cannot be influenced by
        prompt content.
        """
        text_lower = patient_text.lower()
        for symptom in self.patient_record.red_flag_symptoms:
            pattern = r"\b" + re.escape(symptom.lower()) + r"\b"
            if re.search(pattern, text_lower):
                return symptom
        return None

    def advance(self) -> ConversationState:
        """Move to the next state in the normal linear progression.

        Raises InvalidTransitionError if called from the terminal state
        (CLOSING), which has no successor.
        """
        next_state = _NEXT_STATE[self.state]
        if next_state is None:
            raise InvalidTransitionError(
                f"Cannot advance from terminal state {self.state.value}"
            )
        self.state = next_state
        return self.state

    def handle_patient_message(self, patient_text: str) -> ConversationState:
        """Process one patient utterance and return the resulting state.

        If the message matches a red-flag symptom, this forces an
        immediate transition to ESCALATION_CHECK regardless of the
        current state (unless already in CLOSING, which is terminal).
        This override is independent of and takes priority over normal
        linear progression.
        """
        flag = self.check_for_red_flag(patient_text)
        if flag is not None and self.state != ConversationState.CLOSING:
            self.state = ConversationState.ESCALATION_CHECK
            self.escalated = True
            self._escalation_reason = flag
            return self.state

        return self.advance()
