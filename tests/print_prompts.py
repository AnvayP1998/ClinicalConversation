"""Manual review script: prints each state's fully rendered prompt with the
synthetic patient record injected, so the actual prompt language can be
reviewed before any Claude integration is wired up.

Run with: python tests/print_prompts.py
This is not a pytest test (no test_ functions) and is not collected by pytest.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.patient_record import PatientRecord
from app.prompt_loader import render_prompt
from app.state_machine import ConversationState

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "patient_record.json"


def main() -> None:
    raw = json.loads(DATA_PATH.read_text())
    patient = PatientRecord(**raw)

    for state in ConversationState:
        print("=" * 80)
        print(f"STATE: {state.value}")
        print("=" * 80)
        print(render_prompt(state, patient))
        print()


if __name__ == "__main__":
    main()
