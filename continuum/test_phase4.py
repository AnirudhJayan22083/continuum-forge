"""
test_phase4.py

Phase 4 test suite for CONTINUUM — ValidationEngine, the statistical
core of the project.

Two layers of testing:
  1. Unit tests on individual statistical building blocks, with crafted
     inputs that isolate each edge case (zero variance, degenerate
     tables, decision-logic branches) precisely.
  2. Integration tests against the real Phase 1 synthetic dataset,
     confirming the true bearing pattern is Accepted and the false
     "every Tuesday" pattern is Rejected end-to-end.

Run with:
    python test_phase4.py
"""

import shutil
import sys
from datetime import datetime

from agents.validation import ValidationEngine, ValidationInputError
from database.sqlite import Database
from models.heuristic import Heuristic, HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from utils.synthetic_data import SyntheticDataGenerator

TEST_DATA_DIR = "data_phase4_test"
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


def make_log(log_id: str, hour: int, failure_type: str, machine_id: str = "MACHINE-A") -> MaintenanceLog:
    """Build a MaintenanceLog with a controlled hour-of-day, for tests
    that use the derived 'hour' attribute rather than sensor joins."""
    return MaintenanceLog(
        log_id=log_id,
        machine_id=machine_id,
        component="bearing",
        failure_type=failure_type,
        timestamp=datetime(2026, 1, 1, hour, 0, 0),
        description="test log",
        technician_id="EMP001",
        resolution="test resolution",
    )


# ----------------------------------------------------------------------
# Unit tests: contingency table
# ----------------------------------------------------------------------

def test_build_contingency_table() -> None:
    section("Testing _build_contingency_table (unit)...")

    condition_flags = [1, 1, 0, 0, 1, 0]
    failure_flags = [1, 0, 1, 0, 1, 0]
    a, b, c, d = ValidationEngine._build_contingency_table(condition_flags, failure_flags)

    check(f"a (condition & failure) = {a}", a == 2)
    check(f"b (condition & no failure) = {b}", b == 1)
    check(f"c (no condition & failure) = {c}", c == 1)
    check(f"d (no condition & no failure) = {d}", d == 2)
    check("a+b+c+d equals total observations", a + b + c + d == len(condition_flags))


# ----------------------------------------------------------------------
# Unit tests: Pearson correlation edge cases
# ----------------------------------------------------------------------

def test_pearson_correlation_zero_variance() -> None:
    section("Testing _safe_pearson_correlation edge cases (unit)...")

    all_condition_true = ValidationEngine._safe_pearson_correlation([1, 1, 1, 1], [1, 0, 1, 0])
    check("Zero-variance condition (always true) returns 0.0, not NaN/crash", all_condition_true == 0.0)

    all_failure_true = ValidationEngine._safe_pearson_correlation([1, 0, 1, 0], [1, 1, 1, 1])
    check("Zero-variance failure flag (always true) returns 0.0, not NaN/crash", all_failure_true == 0.0)

    normal_case = ValidationEngine._safe_pearson_correlation([1, 1, 0, 0], [1, 1, 0, 0])
    check("Perfectly correlated inputs return 1.0", abs(normal_case - 1.0) < 1e-9)


# ----------------------------------------------------------------------
# Unit tests: chi-square edge cases
# ----------------------------------------------------------------------

def test_chi_square_degenerate_table() -> None:
    section("Testing _safe_chi_square degenerate table handling (unit)...")

    # Zero column (condition never met: a=b=0) -> degenerate, should not crash
    chi2, p = ValidationEngine._safe_chi_square(a=0, b=0, c=5, d=10)
    check("Degenerate table (zero column) returns safe fallback (p=1.0)", p == 1.0 and chi2 == 0.0)

    # Zero row (no failures at all: a=c=0) -> degenerate, should not crash
    chi2, p = ValidationEngine._safe_chi_square(a=0, b=5, c=0, d=10)
    check("Degenerate table (zero row) returns safe fallback (p=1.0)", p == 1.0 and chi2 == 0.0)

    # Normal, well-formed table should produce a real chi-square result
    chi2, p = ValidationEngine._safe_chi_square(a=23, b=8, c=7, d=54)
    check(f"Well-formed table produces a real chi-square statistic ({chi2:.2f})", chi2 > 0)
    check(f"Well-formed table produces a real p-value ({p:.6f})", 0 <= p <= 1)


# ----------------------------------------------------------------------
# Unit tests: confidence score
# ----------------------------------------------------------------------

def test_confidence_score_bounds() -> None:
    section("Testing _compute_confidence_score bounds (unit)...")

    best_case = ValidationEngine._compute_confidence_score(
        conditional_probability=1.0, p_value=0.0, pearson_correlation=1.0
    )
    check(f"Best-case inputs produce score near 1.0 ({best_case:.4f})", abs(best_case - 1.0) < 1e-9)

    worst_case = ValidationEngine._compute_confidence_score(
        conditional_probability=0.0, p_value=1.0, pearson_correlation=0.0
    )
    check(f"Worst-case inputs produce score of 0.0 ({worst_case:.4f})", worst_case == 0.0)

    mid_case = ValidationEngine._compute_confidence_score(
        conditional_probability=0.5, p_value=0.5, pearson_correlation=0.5
    )
    check(f"Score stays within [0, 1] for mid-range inputs ({mid_case:.4f})", 0.0 <= mid_case <= 1.0)


# ----------------------------------------------------------------------
# Unit tests: decision logic
# ----------------------------------------------------------------------

def test_decision_logic() -> None:
    section("Testing _decide branch coverage (unit)...")

    engine = ValidationEngine(db=None, p_value_threshold=0.05, min_support_count=5)

    # All three conditions met -> Accepted
    decision = engine._decide(
        chi_square_p_value=0.001, support_count=10, conditional_probability=0.8, baseline_rate=0.3
    )
    check("All conditions met -> Accepted", decision == "Accepted")

    # Not statistically significant -> Rejected
    decision = engine._decide(
        chi_square_p_value=0.5, support_count=10, conditional_probability=0.8, baseline_rate=0.3
    )
    check("Not significant (p=0.5) -> Rejected", decision == "Rejected")

    # Not enough support, even though significant and beats baseline -> Rejected
    decision = engine._decide(
        chi_square_p_value=0.001, support_count=2, conditional_probability=0.8, baseline_rate=0.3
    )
    check("Insufficient support_count (2 < 5) -> Rejected", decision == "Rejected")

    # Significant and enough support, but doesn't beat baseline -> Rejected
    decision = engine._decide(
        chi_square_p_value=0.001, support_count=10, conditional_probability=0.3, baseline_rate=0.5
    )
    check("Conditional probability does not beat baseline -> Rejected", decision == "Rejected")


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


def test_true_heuristic_accepted(db: Database) -> None:
    section("Testing TRUE heuristic (bearing pattern) is Accepted (integration)...")

    engine = ValidationEngine(db=db)
    heuristic = Heuristic(
        heuristic_id="HEU_TRUE", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Humidity > 80% AND Increasing vibration",
        conditions=[
            HeuristicCondition(parameter="humidity_percent", operator=">", value=80),
            HeuristicCondition(parameter="vibration_mm_s", operator=">", value=2.0),
        ],
        symptoms=["overheating", "noise"], recommended_action="Replace bearing",
        expert_confidence=0.95, extracted_from_interview="INT001",
        extraction_timestamp="2026-07-20T15:00:00",
    )

    result = engine.validate(heuristic, validation_id="VAL_TRUE", validation_timestamp="2026-07-25T12:00:00")

    check(f"Decision is Accepted (got: {result.decision})", result.decision == "Accepted")
    check(f"Chi-square p-value is significant ({result.chi_square_p_value:.6f})", result.chi_square_p_value < 0.05)
    check(f"Pearson correlation is positive ({result.pearson_correlation})", result.pearson_correlation > 0)
    check(f"Support count meets minimum ({result.support_count})", result.support_count >= 5)


def test_false_heuristic_rejected(db: Database) -> None:
    section("Testing FALSE heuristic (every Tuesday) is Rejected (integration)...")

    engine = ValidationEngine(db=db)
    heuristic = Heuristic(
        heuristic_id="HEU_FALSE", machine_id="MACHINE-B", component="seal",
        failure_type="bearing_failure", trigger="Failures increase every Tuesday",
        conditions=[HeuristicCondition(parameter="day_of_week", operator="==", value=1)],
        symptoms=["none"], recommended_action="Monitor",
        expert_confidence=0.4, extracted_from_interview="INT002",
        extraction_timestamp="2026-07-21T10:30:00",
    )

    result = engine.validate(heuristic, validation_id="VAL_FALSE", validation_timestamp="2026-07-25T12:00:00")

    check(f"Decision is Rejected (got: {result.decision})", result.decision == "Rejected")
    check(f"Chi-square p-value is NOT significant ({result.chi_square_p_value:.6f})", result.chi_square_p_value >= 0.05)


def test_unknown_parameter_raises(db: Database) -> None:
    section("Testing unknown condition parameter raises ValidationInputError (integration)...")

    engine = ValidationEngine(db=db)
    heuristic = Heuristic(
        heuristic_id="HEU_BAD", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="nonsense",
        conditions=[HeuristicCondition(parameter="lunar_phase", operator="==", value=1)],
        symptoms=[], recommended_action="n/a", expert_confidence=0.5,
        extracted_from_interview="INT001", extraction_timestamp="2026-07-20T15:00:00",
    )

    try:
        engine.validate(heuristic, validation_id="VAL_BAD", validation_timestamp="2026-07-25T12:00:00")
        check("Unknown parameter raises ValidationInputError", False)
    except ValidationInputError:
        check("Unknown parameter raises ValidationInputError", True)


def test_no_historical_data_raises() -> None:
    section("Testing empty historical data raises ValueError (integration)...")

    empty_db_path = f"{TEST_DATA_DIR}/empty.db"
    db = Database(db_path=empty_db_path)
    db.connect()
    db.init_schema()

    engine = ValidationEngine(db=db)
    heuristic = Heuristic(
        heuristic_id="HEU_EMPTY", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="x",
        conditions=[HeuristicCondition(parameter="humidity_percent", operator=">", value=80)],
        symptoms=[], recommended_action="n/a", expert_confidence=0.5,
        extracted_from_interview="INT001", extraction_timestamp="2026-07-20T15:00:00",
    )

    try:
        engine.validate(heuristic, validation_id="VAL_EMPTY", validation_timestamp="2026-07-25T12:00:00")
        check("Empty database raises ValueError", False)
    except ValueError:
        check("Empty database raises ValueError", True)

    db.close()


def test_min_support_count_enforced() -> None:
    section("Testing min_support_count guard with crafted small-sample data (integration)...")

    # 10 logs total. Condition = "hour == 10". Only 2 logs have hour=10,
    # both are bearing failures (a=2, b=0) -- a "perfect" but tiny sample.
    # 8 remaining logs: 3 are bearing failures (c=3), 5 are not (d=5).
    logs = [
        make_log("L1", hour=10, failure_type="bearing_failure"),
        make_log("L2", hour=10, failure_type="bearing_failure"),
        make_log("L3", hour=2, failure_type="bearing_failure"),
        make_log("L4", hour=3, failure_type="bearing_failure"),
        make_log("L5", hour=4, failure_type="bearing_failure"),
        make_log("L6", hour=5, failure_type="seal_wear"),
        make_log("L7", hour=6, failure_type="seal_wear"),
        make_log("L8", hour=7, failure_type="seal_wear"),
        make_log("L9", hour=8, failure_type="seal_wear"),
        make_log("L10", hour=9, failure_type="seal_wear"),
    ]

    class FakeDatabase:
        def get_maintenance_logs(self, machine_id=None):
            return logs

        def get_sensor_readings(self, machine_id=None):
            return []

    engine = ValidationEngine(db=FakeDatabase(), min_support_count=5)
    heuristic = Heuristic(
        heuristic_id="HEU_SMALL", machine_id="MACHINE-A", component="bearing",
        failure_type="bearing_failure", trigger="Hour == 10",
        conditions=[HeuristicCondition(parameter="hour", operator="==", value=10)],
        symptoms=[], recommended_action="n/a", expert_confidence=0.9,
        extracted_from_interview="INT001", extraction_timestamp="2026-07-20T15:00:00",
    )

    result = engine.validate(heuristic, validation_id="VAL_SMALL", validation_timestamp="2026-07-25T12:00:00")

    check(f"Support count is small ({result.support_count})", result.support_count == 2)
    check(
        f"Rejected despite perfect conditional probability, due to insufficient support "
        f"(got: {result.decision})",
        result.decision == "Rejected",
    )


def cleanup() -> None:
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 4 Test Suite")
    print("=" * 60)

    try:
        # Unit tests (no data setup needed)
        test_build_contingency_table()
        test_pearson_correlation_zero_variance()
        test_chi_square_degenerate_table()
        test_confidence_score_bounds()
        test_decision_logic()
        test_min_support_count_enforced()

        # Integration tests (real synthetic data)
        db = build_real_database()
        test_true_heuristic_accepted(db)
        test_false_heuristic_rejected(db)
        test_unknown_parameter_raises(db)
        db.close()

        test_no_historical_data_raises()
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 4 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 4 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())