"""
test_phase6.py

Phase 6 test suite for CONTINUUM — CodificationAgent.

Exercises, in order:
  1. Codifying an Accepted heuristic correctly builds and inserts an
     OperationalRule, with fields sourced from the right place (e.g.
     confidence_score comes from the ValidationResult, not the
     heuristic's own expert_confidence).
  2. Codifying an equivalent heuristic a second time is correctly
     detected as a duplicate and NOT re-inserted.
  3. Two heuristics that differ only in machine_id are NOT considered
     duplicates of each other (duplicate detection is properly scoped).
  4. Codifying a Rejected (or any non-Accepted) heuristic raises
     CodificationError instead of silently storing it.
  5. The generated diagram is a real, valid, non-trivial PNG file.

Run with:
    python test_phase6.py
"""

import os
import shutil
import sys

from PIL import Image

from agents.codification import CodificationAgent, CodificationError
from database.sqlite import Database
from models.heuristic import Heuristic, HeuristicCondition
from models.validation import ValidationResult

TEST_DATA_DIR = "data_phase6_test"
TEST_DB_PATH = f"{TEST_DATA_DIR}/continuum.db"
TEST_DIAGRAMS_DIR = f"{TEST_DATA_DIR}/diagrams"

PASS = "\u2713"
FAIL = "\u2717"


def section(title: str) -> None:
    print(f"\n{title}")


def check(label: str, condition: bool) -> None:
    mark = PASS if condition else FAIL
    print(f"{mark} {label}")
    if not condition:
        raise AssertionError(f"FAILED: {label}")


def make_heuristic(heuristic_id: str = "HEU_TRUE", machine_id: str = "MACHINE-A") -> Heuristic:
    return Heuristic(
        heuristic_id=heuristic_id, machine_id=machine_id, component="bearing",
        failure_type="bearing_failure", trigger="Humidity > 80% AND Increasing vibration",
        conditions=[
            HeuristicCondition(parameter="humidity_percent", operator=">", value=80),
            HeuristicCondition(parameter="vibration_mm_s", operator=">", value=2.0),
        ],
        symptoms=["overheating", "noise", "vibration"],
        recommended_action="Replace bearing and clean lubrication system",
        expert_confidence=0.95, extracted_from_interview="INT001",
        extraction_timestamp="2026-07-20T15:00:00",
    )


def make_validation_result(decision: str = "Accepted", confidence_score: float = 0.80) -> ValidationResult:
    return ValidationResult(
        validation_id="VAL_TRUE", heuristic_id="HEU_TRUE",
        support_count=31, total_occurrences=92, conditional_probability=0.742,
        pearson_correlation=0.632, chi_square_statistic=33.99, chi_square_p_value=0.0000004,
        confidence_score=confidence_score, decision=decision, reasoning="strong statistical support",
        validation_timestamp="2026-07-25T12:00:00",
    )


def build_db() -> Database:
    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()
    return db


def test_codify_accepted_heuristic() -> None:
    section("Testing codify() with an Accepted heuristic...")

    db = build_db()
    agent = CodificationAgent(db=db, diagrams_dir=TEST_DIAGRAMS_DIR)

    heuristic = make_heuristic()
    validation_result = make_validation_result(confidence_score=0.80)

    result = agent.codify(
        heuristic, validation_result, rule_id="RULE001", created_timestamp="2026-07-25T13:00:00"
    )

    check("Rule was inserted (not a duplicate)", result.inserted is True)
    check("Rule's machine_id matches heuristic's", result.rule.machine_id == "MACHINE-A")
    check("Rule's trigger matches heuristic's", result.rule.trigger == heuristic.trigger)
    check(
        "Rule's confidence_score comes from ValidationResult, not Heuristic.expert_confidence",
        result.rule.confidence_score == 0.80 and result.rule.confidence_score != heuristic.expert_confidence,
    )

    stored_rules = db.get_operational_rules("MACHINE-A")
    check("Exactly one rule is stored in the database", len(stored_rules) == 1)
    check("Stored rule matches what codify() returned", stored_rules[0].rule_id == "RULE001")

    db.close()


def test_duplicate_detection() -> None:
    section("Testing duplicate detection...")

    db = build_db()
    agent = CodificationAgent(db=db, diagrams_dir=TEST_DIAGRAMS_DIR)

    heuristic = make_heuristic()
    validation_result = make_validation_result()

    result1 = agent.codify(
        heuristic, validation_result, rule_id="RULE001", created_timestamp="2026-07-25T13:00:00"
    )
    check("First codification is inserted", result1.inserted is True)

    result2 = agent.codify(
        heuristic, validation_result, rule_id="RULE002", created_timestamp="2026-07-25T14:00:00"
    )
    check("Second (equivalent) codification is detected as a duplicate", result2.inserted is False)

    stored_rules = db.get_operational_rules("MACHINE-A")
    check(
        f"Database still has exactly 1 rule after duplicate attempt (has {len(stored_rules)})",
        len(stored_rules) == 1,
    )

    db.close()


def test_different_machine_not_a_duplicate() -> None:
    section("Testing duplicate detection is properly scoped by machine_id...")

    db = build_db()
    agent = CodificationAgent(db=db, diagrams_dir=TEST_DIAGRAMS_DIR)

    validation_result = make_validation_result()

    heuristic_a = make_heuristic(heuristic_id="HEU_A", machine_id="MACHINE-A")
    heuristic_b = make_heuristic(heuristic_id="HEU_B", machine_id="MACHINE-B")

    result_a = agent.codify(heuristic_a, validation_result, rule_id="RULE_A", created_timestamp="2026-07-25T13:00:00")
    result_b = agent.codify(heuristic_b, validation_result, rule_id="RULE_B", created_timestamp="2026-07-25T13:00:00")

    check("Rule for MACHINE-A is inserted", result_a.inserted is True)
    check("Rule for MACHINE-B (different machine, same pattern) is ALSO inserted, not a duplicate", result_b.inserted is True)

    total_rules = db.get_operational_rules()
    check(f"Database has both rules (has {len(total_rules)})", len(total_rules) == 2)

    db.close()


def test_rejected_heuristic_raises() -> None:
    section("Testing codify() raises CodificationError for a Rejected heuristic...")

    db = build_db()
    agent = CodificationAgent(db=db, diagrams_dir=TEST_DIAGRAMS_DIR)

    heuristic = make_heuristic()
    rejected_result = make_validation_result(decision="Rejected")

    try:
        agent.codify(
            heuristic, rejected_result, rule_id="RULE_BAD", created_timestamp="2026-07-25T15:00:00"
        )
        check("Rejected heuristic raises CodificationError", False)
    except CodificationError:
        check("Rejected heuristic raises CodificationError", True)

    stored_rules = db.get_operational_rules("MACHINE-A")
    check("Nothing was inserted into the database", len(stored_rules) == 0)

    db.close()


def test_diagram_is_valid_image() -> None:
    section("Testing generated diagram is a valid, well-formed PNG...")

    db = build_db()
    agent = CodificationAgent(db=db, diagrams_dir=TEST_DIAGRAMS_DIR)

    heuristic = make_heuristic()
    validation_result = make_validation_result()

    result = agent.codify(
        heuristic, validation_result, rule_id="RULE_DIAGRAM", created_timestamp="2026-07-25T13:00:00"
    )

    check("Diagram file exists", os.path.exists(result.diagram_path))
    check("Diagram file is non-trivial in size", os.path.getsize(result.diagram_path) > 1000)

    img = Image.open(result.diagram_path)
    check(f"Diagram is a valid PNG ({img.format})", img.format == "PNG")
    check(f"Diagram has real dimensions ({img.size})", img.size[0] > 100 and img.size[1] > 100)
    check("Diagram filename is namespaced by rule_id", "RULE_DIAGRAM" in os.path.basename(result.diagram_path))

    db.close()


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 6 Test Suite")
    print("=" * 60)

    try:
        test_codify_accepted_heuristic()
        cleanup()
        test_duplicate_detection()
        cleanup()
        test_different_machine_not_a_duplicate()
        cleanup()
        test_rejected_heuristic_raises()
        cleanup()
        test_diagram_is_valid_image()
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 6 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 6 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())