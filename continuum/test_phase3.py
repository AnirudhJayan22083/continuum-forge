"""
test_phase3.py

Phase 3 test suite for CONTINUUM.

Exercises, in order:
  1. Happy path — MockClaudeClient's extraction branch produces a valid Heuristic.
  2. Markdown-fenced JSON is still parsed correctly (```json ... ```).
  3. Non-JSON response raises ExtractionError, not a silent fallback.
  4. Out-of-schema JSON (bad confidence, missing field) raises ExtractionError,
     not a wrong exception type or a silently-clamped value.
  5. Database round-trip for the extracted Heuristic.

Run with:
    python test_phase3.py
"""

import shutil
import sys

from agents.extraction import ExtractionError, KnowledgeExtractionAgent
from database.sqlite import Database
from models.operational_rule import InterviewTranscript
from utils.claude_client import ClaudeClient, MockClaudeClient

TEST_DATA_DIR = "data_phase3_test"
TEST_DB_PATH = f"{TEST_DATA_DIR}/continuum.db"

PASS = "\u2713"
FAIL = "\u2717"


def section(title: str) -> None:
    print(f"\n{title}")


def check(label: str, condition: bool) -> None:
    mark = PASS if condition else FAIL
    print(f"{mark} {label}")
    if not condition:
        raise AssertionError(f"FAILED: {label}")


def build_test_transcript() -> InterviewTranscript:
    return InterviewTranscript(
        interview_id="INT001",
        employee_id="EMP001",
        incident_id="LOG0001",
        transcript=(
            "Q: What happened?\n"
            "A: Humidity was 85%, vibration hit 2.3mm/s, bearing overheated."
        ),
        timestamp="2026-07-20T15:00:00",
    )


class FixedResponseClient(ClaudeClient):
    """Test double that returns a fixed string regardless of prompt."""

    def __init__(self, response: str):
        self._response = response

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        return self._response


def test_happy_path_extraction() -> "Heuristic":
    section("Testing happy-path extraction (MockClaudeClient)...")

    transcript = build_test_transcript()
    agent = KnowledgeExtractionAgent(claude_client=MockClaudeClient())

    heuristic = agent.extract_heuristic(
        transcript=transcript,
        heuristic_id="HEU001",
        machine_id="MACHINE-A",
        extraction_timestamp="2026-07-20T15:30:00",
    )

    check("component extracted correctly", heuristic.component == "bearing")
    check("failure_type extracted correctly", heuristic.failure_type == "bearing_failure")
    check("conditions has 2 entries", len(heuristic.conditions) == 2)
    check(
        "conditions reference humidity_percent and vibration_mm_s",
        {c.parameter for c in heuristic.conditions} == {"humidity_percent", "vibration_mm_s"},
    )
    check("expert_confidence in valid range", 0 <= heuristic.expert_confidence <= 1)
    check("extracted_from_interview links back to transcript", heuristic.extracted_from_interview == "INT001")
    check("machine_id is the caller-supplied value, not guessed", heuristic.machine_id == "MACHINE-A")

    return heuristic


def test_markdown_fenced_json() -> None:
    section("Testing markdown code-fenced JSON is parsed correctly...")

    fenced_response = (
        "```json\n"
        "{\n"
        '  "component": "seal",\n'
        '  "failure_type": "seal_wear",\n'
        '  "trigger": "Pressure drop with rising temperature",\n'
        '  "conditions": [{"parameter": "pressure_bar", "operator": "<", "value": 5.0}],\n'
        '  "symptoms": ["pressure fluctuation"],\n'
        '  "recommended_action": "Replace seal",\n'
        '  "expert_confidence": 0.6\n'
        "}\n"
        "```"
    )
    agent = KnowledgeExtractionAgent(claude_client=FixedResponseClient(fenced_response))
    transcript = build_test_transcript()

    heuristic = agent.extract_heuristic(
        transcript=transcript,
        heuristic_id="HEU002",
        machine_id="MACHINE-B",
        extraction_timestamp="2026-07-21T10:30:00",
    )
    check("component parsed correctly through code fence", heuristic.component == "seal")
    check("conditions parsed correctly through code fence", heuristic.conditions[0].parameter == "pressure_bar")


def test_non_json_response_raises() -> None:
    section("Testing non-JSON response raises ExtractionError...")

    agent = KnowledgeExtractionAgent(
        claude_client=FixedResponseClient("Sorry, I cannot help with that.")
    )
    transcript = build_test_transcript()

    try:
        agent.extract_heuristic(
            transcript=transcript,
            heuristic_id="HEU_BAD",
            machine_id="MACHINE-A",
            extraction_timestamp="2026-07-20T15:30:00",
        )
        check("Non-JSON response raises ExtractionError", False)
    except ExtractionError:
        check("Non-JSON response raises ExtractionError", True)


def test_out_of_range_confidence_raises() -> None:
    section("Testing out-of-range confidence raises ExtractionError...")

    bad_json = (
        '{"component": "bearing", "failure_type": "bearing_failure", '
        '"trigger": "x", "conditions": [], "symptoms": [], '
        '"recommended_action": "y", "expert_confidence": 5.0}'
    )
    agent = KnowledgeExtractionAgent(claude_client=FixedResponseClient(bad_json))
    transcript = build_test_transcript()

    try:
        agent.extract_heuristic(
            transcript=transcript,
            heuristic_id="HEU_BAD2",
            machine_id="MACHINE-A",
            extraction_timestamp="2026-07-20T15:30:00",
        )
        check("Confidence 5.0 raises ExtractionError", False)
    except ExtractionError:
        check("Confidence 5.0 raises ExtractionError", True)
    except Exception as exc:  # noqa: BLE001 - intentionally checking wrong-exception-type case
        check(f"Wrong exception type raised: {type(exc).__name__} (expected ExtractionError)", False)


def test_missing_field_raises() -> None:
    section("Testing missing required field raises ExtractionError...")

    incomplete_json = '{"component": "bearing", "failure_type": "bearing_failure"}'
    agent = KnowledgeExtractionAgent(claude_client=FixedResponseClient(incomplete_json))
    transcript = build_test_transcript()

    try:
        agent.extract_heuristic(
            transcript=transcript,
            heuristic_id="HEU_BAD3",
            machine_id="MACHINE-A",
            extraction_timestamp="2026-07-20T15:30:00",
        )
        check("Missing 'trigger'/'conditions'/etc. raises ExtractionError", False)
    except ExtractionError:
        check("Missing 'trigger'/'conditions'/etc. raises ExtractionError", True)


def test_database_round_trip(heuristic) -> None:
    section("Testing database round-trip for extracted Heuristic...")

    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()
    db.insert_heuristic(heuristic)

    fetched = db.get_heuristic(heuristic.heuristic_id)
    check("Heuristic fetched from database is not None", fetched is not None)
    check("Fetched component matches", fetched.component == heuristic.component)
    check(
        "Fetched conditions match (nested objects preserved)",
        [(c.parameter, c.operator, c.value) for c in fetched.conditions]
        == [(c.parameter, c.operator, c.value) for c in heuristic.conditions],
    )

    db.close()


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 3 Test Suite")
    print("=" * 60)

    try:
        heuristic = test_happy_path_extraction()
        test_markdown_fenced_json()
        test_non_json_response_raises()
        test_out_of_range_confidence_raises()
        test_missing_field_raises()
        test_database_round_trip(heuristic)
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 3 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 3 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())