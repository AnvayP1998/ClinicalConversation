import json
from pathlib import Path

import pytest

from app.patient_record import PatientRecord
from app.state_machine import ConversationState, InvalidTransitionError, StateMachine

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "patient_record.json"


@pytest.fixture
def patient() -> PatientRecord:
    raw = json.loads(DATA_PATH.read_text())
    return PatientRecord(**raw)


def test_normal_state_progression(patient):
    sm = StateMachine(patient)
    assert sm.state == ConversationState.GREETING

    assert sm.advance() == ConversationState.VERIFY_IDENTITY
    assert sm.advance() == ConversationState.MEDICATION_CHECK
    assert sm.advance() == ConversationState.SIDE_EFFECT_CHECK
    assert sm.advance() == ConversationState.ESCALATION_CHECK
    assert sm.advance() == ConversationState.CLOSING


def test_advance_from_closing_raises_invalid_transition(patient):
    sm = StateMachine(patient, state=ConversationState.CLOSING)

    with pytest.raises(InvalidTransitionError):
        sm.advance()


@pytest.mark.parametrize(
    "starting_state",
    [
        ConversationState.GREETING,
        ConversationState.VERIFY_IDENTITY,
        ConversationState.MEDICATION_CHECK,
        ConversationState.SIDE_EFFECT_CHECK,
    ],
)
def test_red_flag_forces_escalation_override_from_any_state(patient, starting_state):
    sm = StateMachine(patient, state=starting_state)

    # "shortness of breath" is in the synthetic patient's red_flag_symptoms.
    new_state = sm.handle_patient_message(
        "I've been having some shortness of breath since yesterday."
    )

    assert new_state == ConversationState.ESCALATION_CHECK
    assert sm.state == ConversationState.ESCALATION_CHECK
    assert sm.escalated is True


def test_red_flag_override_is_case_insensitive_and_substring_safe(patient):
    sm = StateMachine(patient, state=ConversationState.MEDICATION_CHECK)

    new_state = sm.handle_patient_message("I had CHEST PAIN this morning.")

    assert new_state == ConversationState.ESCALATION_CHECK


def test_red_flag_does_not_trigger_from_closing_state(patient):
    sm = StateMachine(patient, state=ConversationState.CLOSING)

    # CLOSING is terminal; a red-flag mention here should not "re-enter"
    # escalation. Since CLOSING has no successor, advancing raises.
    with pytest.raises(InvalidTransitionError):
        sm.handle_patient_message("I have chest pain.")

    assert sm.escalated is False


def test_non_red_flag_message_advances_normally(patient):
    sm = StateMachine(patient, state=ConversationState.GREETING)

    new_state = sm.handle_patient_message("Yes, I'm ready to talk now.")

    assert new_state == ConversationState.VERIFY_IDENTITY
    assert sm.escalated is False


def test_unrelated_symptom_word_does_not_false_positive(patient):
    sm = StateMachine(patient, state=ConversationState.MEDICATION_CHECK)

    # "tired" is not one of this patient's red_flag_symptoms.
    new_state = sm.handle_patient_message("I've been feeling a little tired.")

    assert new_state == ConversationState.SIDE_EFFECT_CHECK
    assert sm.escalated is False


def test_word_boundary_prevents_partial_word_match(patient):
    sm = StateMachine(patient, state=ConversationState.MEDICATION_CHECK)

    # "fainting" is a red flag; "faintingly" should not spuriously exist,
    # but ensure a substring embedded in an unrelated longer word doesn't
    # false-positive on a symptom like "swelling" via "unswelling"-style text.
    new_state = sm.handle_patient_message("I am not swellingXYZ or anything unusual.")

    assert new_state == ConversationState.SIDE_EFFECT_CHECK
    assert sm.escalated is False
