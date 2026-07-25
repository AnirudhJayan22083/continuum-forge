"""
test_phase7.py

Phase 7 test suite for CONTINUUM — MentorAgent.

Exercises, in order:
  1. A live reading matching a rule's conditions produces a correct
     recommendation (confidence, action, supporting incidents).
  2. A live reading NOT matching any rule produces an empty list, not
     an error.
  3. A reading matching only SOME of an AND'd condition set still
     correctly counts as no match.
  4. get_best_recommendation returns the single top match, or None.
  5. Multiple matching rules are ranked by confidence, highest first.
  6. A machine with no stored rules at all returns an empty list.
  7. An unrecognized condition parameter on a stored rule raises
     MentorInputError rather than silently mismatching or crashing.

Run with:
    python test_phase7.py
"""

import shutil
import sys

from agents.mentor import MentorAgent, MentorInputError
from database.sqlite import Database
from models.heuristic import HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from models.operational_rule import OperationalRule

TEST_DATA_DIR = "data_phase7_test"
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


def build_db() -> Database:
    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()
    return db


def make_reading(
    reading_id: str, machine_id: str, humidity: float, vibration: float
) -> SensorReading:
    return SensorReading(
        reading_id=reading_id, machine_id=machine_id, timestamp="2026-07-25T14:00:00",
        humidity_percent=humidity, vibration_mm_s=vibration,
        temperature_celsius=75.0, pressure_bar=6.0,
    )


def seed_bearing_rule(db: Database, rule_id: str = "RULE001", confidence: float = 0.80) -> None:
    db.insert_operational_rule(
        OperationalRule(
            rule_id=rule_id, heuristic_id="HEU_TRUE", machine_id="MACHINE-A",
            component="bearing", failure_type="bearing_failure",
            trigger="Humidity > 80% AND Increasing vibration",
            conditions=[
                HeuristicCondition(parameter="humidity_percent", operator=">", value=80),
                HeuristicCondition(parameter="vibration_mm_s", operator=">", value=2.0),
            ],
            recommended_action="Replace bearing and clean lubrication system",
            confidence_score=confidence, created_timestamp="2026-07-25T13:00:00",
        )
    )


def seed_historical_logs(db: Database, count: int = 3) -> None:
    for i in range(count):
        db.insert_maintenance_log(
            MaintenanceLog(
                log_id=f"LOG{i+1:04d}", machine_id="MACHINE-A", component="bearing",
                failure_type="bearing_failure", timestamp=f"2026-0{i+1}-05T10:00:00",
                description="Bearing overheated due to high humidity and vibration",
                technician_id="EMP001", resolution="Replaced bearing",
            )
        )


def test_matching_reading_produces_recommendation() -> None:
    section("Testing a matching live reading produces a correct recommendation...")

    db = build_db()
    seed_bearing_rule(db)
    seed_historical_logs(db, count=3)
    mentor = MentorAgent(db=db)

    risky_reading = make_reading("LIVE001", "MACHINE-A", humidity=88.0, vibration=2.5)
    recommendations = mentor.get_recommendations("MACHINE-A", risky_reading)

    check(f"Exactly one recommendation returned ({len(recommendations)})", len(recommendations) == 1)
    rec = recommendations[0]
    check("Recommendation references the correct rule", rec.rule_id == "RULE001")
    check("Confidence matches the rule's stored confidence", rec.confidence == 0.80)
    check(
        "Recommended action matches the rule's action",
        rec.recommended_action == "Replace bearing and clean lubrication system",
    )
    check(f"Supporting incidents populated (found {len(rec.supporting_incidents)})", len(rec.supporting_incidents) == 3)
    check("Explanation references the trigger", "Humidity > 80%" in rec.explanation)
    check("Explanation references the recommended action", "Replace bearing" in rec.explanation)

    db.close()


def test_non_matching_reading_returns_empty() -> None:
    section("Testing a non-matching live reading returns an empty list...")

    db = build_db()
    seed_bearing_rule(db)
    mentor = MentorAgent(db=db)

    normal_reading = make_reading("LIVE002", "MACHINE-A", humidity=45.0, vibration=0.8)
    recommendations = mentor.get_recommendations("MACHINE-A", normal_reading)

    check("No recommendations for a normal reading", recommendations == [])

    db.close()


def test_partial_match_does_not_count() -> None:
    section("Testing a reading matching only SOME conditions still returns no match...")

    db = build_db()
    seed_bearing_rule(db)
    mentor = MentorAgent(db=db)

    # High humidity but normal vibration -- only one of two AND'd conditions holds.
    partial_reading = make_reading("LIVE003", "MACHINE-A", humidity=90.0, vibration=1.0)
    recommendations = mentor.get_recommendations("MACHINE-A", partial_reading)

    check("Partial match (only 1 of 2 AND'd conditions) does not count as a match", recommendations == [])

    db.close()


def test_get_best_recommendation() -> None:
    section("Testing get_best_recommendation convenience method...")

    db = build_db()
    seed_bearing_rule(db)
    mentor = MentorAgent(db=db)

    risky_reading = make_reading("LIVE001", "MACHINE-A", humidity=88.0, vibration=2.5)
    normal_reading = make_reading("LIVE002", "MACHINE-A", humidity=45.0, vibration=0.8)

    best_match = mentor.get_best_recommendation("MACHINE-A", risky_reading)
    check("Best recommendation found for matching reading", best_match is not None and best_match.rule_id == "RULE001")

    best_no_match = mentor.get_best_recommendation("MACHINE-A", normal_reading)
    check("None returned for non-matching reading", best_no_match is None)

    db.close()


def test_multiple_matches_ranked_by_confidence() -> None:
    section("Testing multiple matching rules are ranked by confidence, highest first...")

    db = build_db()
    seed_bearing_rule(db, rule_id="RULE_LOW", confidence=0.55)
    db.insert_operational_rule(
        OperationalRule(
            rule_id="RULE_HIGH", heuristic_id="HEU_HIGH", machine_id="MACHINE-A",
            component="bearing", failure_type="bearing_failure",
            trigger="Humidity > 85%",
            conditions=[HeuristicCondition(parameter="humidity_percent", operator=">", value=85)],
            recommended_action="Immediate shutdown and inspection",
            confidence_score=0.92, created_timestamp="2026-07-25T13:00:00",
        )
    )
    mentor = MentorAgent(db=db)

    risky_reading = make_reading("LIVE001", "MACHINE-A", humidity=90.0, vibration=2.5)
    recommendations = mentor.get_recommendations("MACHINE-A", risky_reading)

    check(f"Both rules matched ({len(recommendations)})", len(recommendations) == 2)
    check(
        "Highest-confidence rule is ranked first",
        recommendations[0].rule_id == "RULE_HIGH" and recommendations[0].confidence == 0.92,
    )
    check(
        "Lower-confidence rule is ranked second",
        recommendations[1].rule_id == "RULE_LOW" and recommendations[1].confidence == 0.55,
    )

    db.close()


def test_machine_with_no_rules_returns_empty() -> None:
    section("Testing a machine with no stored rules returns an empty list...")

    db = build_db()
    seed_bearing_rule(db)  # only for MACHINE-A
    mentor = MentorAgent(db=db)

    risky_reading = make_reading("LIVE001", "MACHINE-C", humidity=90.0, vibration=2.5)
    recommendations = mentor.get_recommendations("MACHINE-C", risky_reading)

    check("Machine with zero rules returns empty list, not an error", recommendations == [])

    db.close()


def test_unknown_condition_parameter_raises() -> None:
    section("Testing an unrecognized condition parameter raises MentorInputError...")

    db = build_db()
    db.insert_operational_rule(
        OperationalRule(
            rule_id="RULE_BAD", heuristic_id="HEU_BAD", machine_id="MACHINE-A",
            component="bearing", failure_type="bearing_failure",
            trigger="nonsense",
            conditions=[HeuristicCondition(parameter="lunar_phase", operator="==", value=1)],
            recommended_action="n/a", confidence_score=0.5,
            created_timestamp="2026-07-25T13:00:00",
        )
    )
    mentor = MentorAgent(db=db)
    reading = make_reading("LIVE001", "MACHINE-A", humidity=90.0, vibration=2.5)

    try:
        mentor.get_recommendations("MACHINE-A", reading)
        check("Unknown parameter raises MentorInputError", False)
    except MentorInputError:
        check("Unknown parameter raises MentorInputError", True)

    db.close()


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 7 Test Suite")
    print("=" * 60)

    try:
        cleanup()
        test_matching_reading_produces_recommendation()

        cleanup()
        test_non_matching_reading_returns_empty()
        cleanup()
        test_partial_match_does_not_count()
        cleanup()
        test_get_best_recommendation()
        cleanup()
        test_multiple_matches_ranked_by_confidence()
        cleanup()
        test_machine_with_no_rules_returns_empty()
        cleanup()
        test_unknown_condition_parameter_raises()
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 7 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 7 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())