"""
test_phase5.py

Phase 5 test suite for CONTINUUM — ExplainabilityEngine.

Exercises, in order:
  1. _collect_supporting_incidents prioritizes the clearest evidence
     (condition held AND failure occurred) first.
  2. _build_narrative content — correct for both Accepted and Rejected
     decisions, and handles the "no incidents matched" case gracefully.
  3. Chart generation — real files produced, non-trivial size, correct
     paths, no crash on an empty-incidents edge case.
  4. Full explain() integration against real Phase 1 synthetic data for
     both the true bearing heuristic and the false "every Tuesday" one.

Run with:
    python test_phase5.py
"""

import os
import shutil
import sys
from datetime import datetime

from agents.explainability import ExplainabilityEngine, SupportingIncident
from agents.validation import ValidationEngine
from database.sqlite import Database
from models.heuristic import Heuristic, HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from models.validation import ValidationResult
from utils.synthetic_data import SyntheticDataGenerator

TEST_DATA_DIR = "data_phase5_test"
TEST_DB_PATH = f"{TEST_DATA_DIR}/continuum.db"
TEST_CHARTS_DIR = f"{TEST_DATA_DIR}/charts"

PASS = "\u2713"
FAIL = "\u2717"


def section(title: str) -> None:
    print(f"\n{title}")


def check(label: str, condition: bool) -> None:
    mark = PASS if condition else FAIL
    print(f"{mark} {label}")
    if not condition:
        raise AssertionError(f"FAILED: {label}")


def make_log(log_id: str, machine_id: str, failure_type: str, hour: int = 12) -> MaintenanceLog:
    return MaintenanceLog(
        log_id=log_id, machine_id=machine_id, component="bearing",
        failure_type=failure_type, timestamp=datetime(2026, 1, 1, hour, 0, 0),
        description=f"description for {log_id}", technician_id="EMP001",
        resolution="resolved",
    )


class FakeDatabase:
    """Minimal Database stand-in exposing only what ExplainabilityEngine needs."""

    def __init__(self, logs=None, readings=None):
        self._logs = logs or []
        self._readings = readings or []

    def get_maintenance_logs(self, machine_id=None):
        return self._logs

    def get_sensor_readings(self, machine_id=None):
        return self._readings


# ----------------------------------------------------------------------
# Unit tests: supporting incident selection
# ----------------------------------------------------------------------

def test_collect_supporting_incidents_prioritizes_best_evidence() -> None:
    section("Testing _collect_supporting_incidents prioritization (unit)...")

    logs = [
        make_log("L1", "MACHINE-A", "seal_wear", hour=1),       # condition won't hold, not target
        make_log("L2", "MACHINE-A", "bearing_failure", hour=10),  # condition WILL hold, target -> best evidence
        make_log("L3", "MACHINE-A", "seal_wear", hour=10),       # condition WILL hold, not target
    ]
    # "hour == 10" condition holds for L2 and L3, not L1.
    heuristic = Heuristic(
        heuristic_id="HEU_TEST", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Hour == 10",
        conditions=[HeuristicCondition(parameter="hour", operator="==", value=10)],
        symptoms=[], recommended_action="n/a", expert_confidence=0.9,
        extracted_from_interview="INT001", extraction_timestamp="2026-01-01T00:00:00",
    )

    db = FakeDatabase(logs=logs, readings=[])
    engine = ValidationEngine(db=db)
    explainer = ExplainabilityEngine(db=db, validation_engine=engine, charts_dir=TEST_CHARTS_DIR)

    incidents = explainer._collect_supporting_incidents(heuristic, logs, [])

    check(f"All 3 logs evaluated (none skipped) -> {len(incidents)} incidents", len(incidents) == 3)
    check(
        "Best evidence (condition held AND target failure) is ranked first",
        incidents[0].log_id == "L2" and incidents[0].condition_held and incidents[0].failure_type == "bearing_failure",
    )


# ----------------------------------------------------------------------
# Unit tests: narrative content
# ----------------------------------------------------------------------

def make_validation_result(decision: str, reasoning: str) -> ValidationResult:
    return ValidationResult(
        validation_id="VAL_TEST", heuristic_id="HEU_TEST",
        support_count=10, total_occurrences=50,
        conditional_probability=0.7, pearson_correlation=0.5,
        chi_square_statistic=12.3, chi_square_p_value=0.001,
        confidence_score=0.75, decision=decision, reasoning=reasoning,
        validation_timestamp="2026-01-01T00:00:00",
    )


def test_build_narrative_accepted() -> None:
    section("Testing _build_narrative for an Accepted decision (unit)...")

    heuristic = Heuristic(
        heuristic_id="HEU_TEST", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Humidity > 80%",
        conditions=[HeuristicCondition(parameter="humidity_percent", operator=">", value=80)],
        symptoms=[], recommended_action="Replace bearing", expert_confidence=0.9,
        extracted_from_interview="INT001", extraction_timestamp="2026-01-01T00:00:00",
    )
    result = make_validation_result("Accepted", "Accepted: strong statistical support.")
    incidents = [
        SupportingIncident("L1", "MACHINE-A", "2026-01-01T10:00:00", "bearing_failure", True, "desc")
    ]

    narrative = ExplainabilityEngine._build_narrative(heuristic, result, incidents)

    check("Narrative includes the trigger text", "Humidity > 80%" in narrative)
    check("Narrative includes machine/component", "MACHINE-A / bearing" in narrative)
    check("Narrative includes the underlying reasoning", "Accepted: strong statistical support." in narrative)
    check("Narrative cites the supporting incident by log_id", "L1" in narrative)


def test_build_narrative_no_incidents() -> None:
    section("Testing _build_narrative with zero supporting incidents (unit)...")

    heuristic = Heuristic(
        heuristic_id="HEU_TEST", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Humidity > 80%",
        conditions=[HeuristicCondition(parameter="humidity_percent", operator=">", value=80)],
        symptoms=[], recommended_action="Replace bearing", expert_confidence=0.9,
        extracted_from_interview="INT001", extraction_timestamp="2026-01-01T00:00:00",
    )
    result = make_validation_result("Rejected", "Rejected: no significant association.")

    narrative = ExplainabilityEngine._build_narrative(heuristic, result, [])

    check(
        "Narrative handles zero incidents gracefully, no crash",
        "No historical incidents could be matched" in narrative,
    )


# ----------------------------------------------------------------------
# Chart generation
# ----------------------------------------------------------------------

def test_chart_generation_produces_valid_files() -> None:
    section("Testing chart generation produces real, non-trivial files (unit)...")

    logs = [
        make_log("L1", "MACHINE-A", "bearing_failure", hour=10),
        make_log("L2", "MACHINE-A", "seal_wear", hour=2),
        make_log("L3", "MACHINE-A", "bearing_failure", hour=11),
    ]
    heuristic = Heuristic(
        heuristic_id="HEU_CHART_TEST", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Hour >= 10",
        conditions=[HeuristicCondition(parameter="hour", operator=">=", value=10)],
        symptoms=[], recommended_action="n/a", expert_confidence=0.9,
        extracted_from_interview="INT001", extraction_timestamp="2026-01-01T00:00:00",
    )

    db = FakeDatabase(logs=logs, readings=[])
    engine = ValidationEngine(db=db)
    explainer = ExplainabilityEngine(db=db, validation_engine=engine, charts_dir=TEST_CHARTS_DIR)

    timeline_path = explainer._generate_timeline_chart(heuristic, logs, [])
    result = make_validation_result("Accepted", "test reasoning")
    probability_path = explainer._generate_probability_chart(heuristic, result)

    check(f"Timeline chart file exists ({timeline_path})", timeline_path.exists())
    check("Timeline chart file is non-trivial in size", timeline_path.stat().st_size > 1000)
    check(f"Probability chart file exists ({probability_path})", probability_path.exists())
    check("Probability chart file is non-trivial in size", probability_path.stat().st_size > 1000)
    check(
        "Chart filenames are namespaced by heuristic_id",
        "HEU_CHART_TEST" in timeline_path.name and "HEU_CHART_TEST" in probability_path.name,
    )


# ----------------------------------------------------------------------
# Integration tests against real synthetic data
# ----------------------------------------------------------------------

def build_real_database() -> Database:
    gen = SyntheticDataGenerator(data_dir=TEST_DATA_DIR)
    logs_raw = gen.generate_maintenance_logs()
    readings_raw = gen.generate_sensor_history(logs_raw)

    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()

    for raw in logs_raw:
        db.insert_maintenance_log(
            MaintenanceLog(
                log_id=raw["log_id"], machine_id=raw["machine_id"], component=raw["component"],
                failure_type=raw["failure_type"], timestamp=raw["timestamp"],
                description=raw["description"], technician_id=raw["technician_id"],
                resolution=raw["resolution"],
            )
        )
    for raw in readings_raw:
        db.insert_sensor_reading(
            SensorReading(
                reading_id=raw["reading_id"], machine_id=raw["machine_id"], timestamp=raw["timestamp"],
                humidity_percent=raw["humidity_percent"], vibration_mm_s=raw["vibration_mm_s"],
                temperature_celsius=raw["temperature_celsius"], pressure_bar=raw["pressure_bar"],
            )
        )
    return db


def test_explain_true_heuristic_end_to_end(db: Database) -> None:
    section("Testing explain() end-to-end for TRUE heuristic (integration)...")

    engine = ValidationEngine(db=db)
    explainer = ExplainabilityEngine(db=db, validation_engine=engine, charts_dir=TEST_CHARTS_DIR)

    heuristic = Heuristic(
        heuristic_id="HEU_TRUE", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Humidity > 80% AND Increasing vibration",
        conditions=[
            HeuristicCondition(parameter="humidity_percent", operator=">", value=80),
            HeuristicCondition(parameter="vibration_mm_s", operator=">", value=2.0),
        ],
        symptoms=["overheating"], recommended_action="Replace bearing",
        expert_confidence=0.95, extracted_from_interview="INT001",
        extraction_timestamp="2026-07-20T15:00:00",
    )
    result = engine.validate(heuristic, validation_id="VAL_TRUE", validation_timestamp="2026-07-25T12:00:00")
    explanation = explainer.explain(heuristic, result)

    check("Decision is Accepted", explanation.decision == "Accepted")
    check("Narrative mentions Accepted", "Accepted" in explanation.narrative)
    check("At least one supporting incident found", len(explanation.supporting_incidents) > 0)
    check("Timeline chart path is a real file", os.path.exists(explanation.timeline_chart_path))
    check("Probability chart path is a real file", os.path.exists(explanation.probability_chart_path))


def test_explain_false_heuristic_end_to_end(db: Database) -> None:
    section("Testing explain() end-to-end for FALSE heuristic (integration)...")

    engine = ValidationEngine(db=db)
    explainer = ExplainabilityEngine(db=db, validation_engine=engine, charts_dir=TEST_CHARTS_DIR)

    heuristic = Heuristic(
        heuristic_id="HEU_FALSE", machine_id="MACHINE-B", component="seal",
        failure_type="bearing_failure", trigger="Failures increase every Tuesday",
        conditions=[HeuristicCondition(parameter="day_of_week", operator="==", value=1)],
        symptoms=["none"], recommended_action="Monitor",
        expert_confidence=0.4, extracted_from_interview="INT002",
        extraction_timestamp="2026-07-21T10:30:00",
    )
    result = engine.validate(heuristic, validation_id="VAL_FALSE", validation_timestamp="2026-07-25T12:00:00")
    explanation = explainer.explain(heuristic, result)

    check("Decision is Rejected", explanation.decision == "Rejected")
    check("Narrative mentions Rejected", "Rejected" in explanation.narrative)
    check("Timeline chart path is a real file", os.path.exists(explanation.timeline_chart_path))
    check("Probability chart path is a real file", os.path.exists(explanation.probability_chart_path))


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 5 Test Suite")
    print("=" * 60)

    try:
        test_collect_supporting_incidents_prioritizes_best_evidence()
        test_build_narrative_accepted()
        test_build_narrative_no_incidents()
        test_chart_generation_produces_valid_files()

        db = build_real_database()
        test_explain_true_heuristic_end_to_end(db)
        test_explain_false_heuristic_end_to_end(db)
        db.close()
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 5 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 5 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())