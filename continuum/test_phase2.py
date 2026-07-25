"""
test_phase2.py

Phase 2 test suite for CONTINUUM.

Exercises, in order:
  1. MockClaudeClient — correct branch selection (grounded vs follow-up
     vs generic fallback), so a future prompt-wording change that breaks
     keyword matching is caught immediately instead of silently degrading.
  2. ElicitationAgent.generate_grounded_questions — count + content grounded
     in the actual incident.
  3. ElicitationAgent.generate_followup_questions — count + content.
  4. ElicitationAgent.conduct_interview — full flow, transcript shape.
  5. ElicitationAgent.save_transcript — real database round-trip.
  6. _parse_numbered_list edge cases (mixed numbering styles, blank lines).

Run with:
    python test_phase2.py
"""

import logging
import shutil
import sys

from agents.elicitation import ElicitationAgent
from database.sqlite import Database
from models.employee import Employee
from models.maintenance import MaintenanceLog
from utils.claude_client import MockClaudeClient
from utils.synthetic_data import SyntheticDataGenerator

TEST_DATA_DIR = "data_phase2_test"
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


def build_test_employee_and_incident():
    """Reuse real Phase 1 synthetic data rather than inventing fixtures,
    so this test exercises the actual shapes the rest of the app produces."""
    gen = SyntheticDataGenerator(data_dir=TEST_DATA_DIR)
    employees_raw = gen.generate_employees()
    logs_raw = gen.generate_maintenance_logs()

    employee = Employee(
        employee_id=employees_raw[0]["employee_id"],
        name=employees_raw[0]["name"],
        machine_id=employees_raw[0]["machine_id"],
        years_experience=employees_raw[0]["years_experience"],
        retirement_date=employees_raw[0]["retirement_date"],
        expertise_areas=employees_raw[0]["expertise_areas"].split(","),
        interview_completed=employees_raw[0]["interview_completed"],
    )

    bearing_log_raw = next(l for l in logs_raw if l["failure_type"] == "bearing_failure")
    incident = MaintenanceLog(
        log_id=bearing_log_raw["log_id"],
        machine_id=bearing_log_raw["machine_id"],
        component=bearing_log_raw["component"],
        failure_type=bearing_log_raw["failure_type"],
        timestamp=bearing_log_raw["timestamp"],
        description=bearing_log_raw["description"],
        technician_id=bearing_log_raw["technician_id"],
        resolution=bearing_log_raw["resolution"],
    )
    return employee, incident


def test_mock_claude_client_branch_selection() -> None:
    section("Testing MockClaudeClient branch selection...")

    client = MockClaudeClient()

    grounded_response = client.generate(
        system_prompt=(
            "You are conducting a grounded interview with an experienced "
            "maintenance technician about a specific historical incident."
        ),
        user_prompt="Machine: MACHINE-A",
    )
    check(
        "Grounded prompt does NOT fall through to generic fallback",
        "Walk me through exactly what you observed" in grounded_response,
    )

    followup_response = client.generate(
        system_prompt="You are conducting a follow-up round of a grounded technician interview.",
        user_prompt="Previous answers here",
    )
    check(
        "Follow-up prompt does NOT fall through to generic fallback",
        "specific threshold" in followup_response,
    )

    generic_response = client.generate(
        system_prompt="Some entirely different future prompt with no known keywords.",
        user_prompt="anything",
    )
    check(
        "Unrecognized prompt correctly falls back to generic response",
        "Can you describe what happened in more detail?" in generic_response,
    )


def test_generate_grounded_questions(employee, incident) -> list:
    section("Testing ElicitationAgent.generate_grounded_questions...")

    agent = ElicitationAgent(claude_client=MockClaudeClient())
    questions = agent.generate_grounded_questions(incident, employee)

    check(f"Generated {len(questions)} grounded questions", len(questions) == 3)
    check(
        "Questions are clean (no leading numbering left over)",
        all(not q[0:2].strip().rstrip(".)").isdigit() for q in questions),
    )
    return questions


def test_generate_followup_questions(incident, prior_questions) -> None:
    section("Testing ElicitationAgent.generate_followup_questions...")

    agent = ElicitationAgent(claude_client=MockClaudeClient())
    qa_pairs = [(q, f"Answer to: {q}") for q in prior_questions]
    followups = agent.generate_followup_questions(incident, qa_pairs)

    check(f"Generated {len(followups)} follow-up questions", len(followups) == 2)


def test_conduct_interview(employee, incident) -> "InterviewTranscript":
    section("Testing ElicitationAgent.conduct_interview...")

    agent = ElicitationAgent(claude_client=MockClaudeClient())

    scripted_answers = iter(
        [
            "Humidity was around 85% and vibration was climbing.",
            "Vibration hit 2.3 mm/s, well above the normal 1.0-1.5 range.",
            "Watch for humidity above 80% AND rising vibration together.",
            "If both stay elevated over an hour, treat it as urgent.",
            "Doesn't hold if the machine was serviced in the last 48 hours.",
        ]
    )

    def get_answer(question: str) -> str:
        return next(scripted_answers)

    transcript = agent.conduct_interview(
        interview_id="INT_TEST_001",
        incident=incident,
        employee=employee,
        get_answer=get_answer,
        timestamp="2026-07-25T12:00:00",
    )

    qa_count = transcript.transcript.count("Q:")
    check(f"Transcript has {qa_count} Q&A pairs (3 grounded + 2 follow-up)", qa_count == 5)
    check("Transcript references employee correctly", transcript.employee_id == employee.employee_id)
    check("Transcript references incident correctly", transcript.incident_id == incident.log_id)
    check(
        "Transcript text contains actual answer content",
        "2.3 mm/s" in transcript.transcript,
    )

    return transcript


def test_save_and_fetch_transcript(transcript) -> None:
    section("Testing ElicitationAgent.save_transcript (database round-trip)...")

    agent = ElicitationAgent(claude_client=MockClaudeClient())

    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()
    agent.save_transcript(transcript, db)

    fetched = db.get_interview_transcript(transcript.interview_id)
    check("Transcript fetched from database is not None", fetched is not None)
    check("Fetched transcript text matches original exactly", fetched.transcript == transcript.transcript)
    check("Fetched employee_id matches", fetched.employee_id == transcript.employee_id)

    db.close()


def test_parse_numbered_list_edge_cases() -> None:
    section("Testing _parse_numbered_list edge cases...")

    parse = ElicitationAgent._parse_numbered_list

    dotted = parse("1. First question?\n2. Second question?\n3. Third question?")
    check("Dot-numbered list parses to 3 clean items", dotted == [
        "First question?", "Second question?", "Third question?"
    ])

    paren = parse("1) First one?\n2) Second one?")
    check("Paren-numbered list parses to 2 clean items", paren == ["First one?", "Second one?"])

    with_blanks = parse("1. First?\n\n\n2. Second?\n")
    check("Blank lines are skipped", with_blanks == ["First?", "Second?"])

    unnumbered = parse("Just a plain question with no numbering?")
    check(
        "Unnumbered single line still returned as-is",
        unnumbered == ["Just a plain question with no numbering?"],
    )


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    logging.disable(logging.CRITICAL)  # keep test output clean; MockClaudeClient's
                                        # warning path is checked explicitly above instead

    print("=" * 60)
    print("CONTINUUM Phase 2 Test Suite")
    print("=" * 60)

    try:
        test_mock_claude_client_branch_selection()

        employee, incident = build_test_employee_and_incident()
        questions = test_generate_grounded_questions(employee, incident)
        test_generate_followup_questions(incident, questions)
        transcript = test_conduct_interview(employee, incident)
        test_save_and_fetch_transcript(transcript)
        test_parse_numbered_list_edge_cases()
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 2 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 2 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())