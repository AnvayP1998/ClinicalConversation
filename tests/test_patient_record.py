import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.patient_record import PatientRecord

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "patient_record.json"


def load_raw_record() -> dict:
    return json.loads(DATA_PATH.read_text())


def test_valid_record_is_accepted():
    raw = load_raw_record()
    record = PatientRecord(**raw)

    assert record.patient_id == "SYN-00042"
    assert record.name == "Jordan Alvarez"
    assert len(record.medications) == 4
    assert "shortness of breath" in record.red_flag_symptoms
    assert record.follow_up_date.isoformat() == "2026-09-29"


def test_missing_required_field_is_rejected():
    raw = load_raw_record()
    del raw["discharge_diagnosis"]

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_missing_name_is_rejected():
    raw = load_raw_record()
    del raw["name"]

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_wrong_type_for_medications_is_rejected():
    raw = load_raw_record()
    raw["medications"] = "Furosemide 40mg daily"

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_wrong_type_for_follow_up_date_is_rejected():
    raw = load_raw_record()
    raw["follow_up_date"] = "not-a-date"

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_empty_medications_list_is_rejected():
    raw = load_raw_record()
    raw["medications"] = []

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_empty_red_flag_symptoms_is_rejected():
    raw = load_raw_record()
    raw["red_flag_symptoms"] = []

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_medication_missing_dosage_is_rejected():
    raw = load_raw_record()
    raw["medications"][0] = {"name": "Furosemide", "frequency": "once daily"}

    with pytest.raises(ValidationError):
        PatientRecord(**raw)


def test_allergies_can_be_empty_list():
    raw = load_raw_record()
    raw["allergies"] = []

    record = PatientRecord(**raw)
    assert record.allergies == []
