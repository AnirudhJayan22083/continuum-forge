"""
test_phase1.py

Phase 1 test suite for CONTINUUM.

Exercises, in order:
  1. Pydantic models (round-trip construction)
  2. Synthetic data generation (counts + embedded pattern strength)
  3. Interview queue generation (ordering)
  4. Database initialization + schema
  5. CSV/JSON file generation

Run with:
    python test_phase1.py
"""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy import stats

from models.employee import Employee
from models.maintenance import MaintenanceLog, SensorReading
from models.heuristic import Heuristic, HeuristicCondition
from models.validation import ValidationResult
from models.operational_rule import OperationalRule, InterviewTranscript
from database.sqlite import Database
from utils.synthetic_data import SyntheticDataGenerator
from utils.interview_queue import InterviewQueueGenerator

TEST_DATA_DIR = "data_phase1_test"
TEST_CONFIG_DIR = "config_phase1_test"
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


def test_models() -> None:
    section("Testing Pydantic models...")

    e = Employee(**Employee.model_config["json_schema_extra"]["example"])
    check("Employee model works", e.name == "John Smith")

    m = MaintenanceLog(**MaintenanceLog.model_config["json_schema_extra"]["example"])
    check("MaintenanceLog model works", m.log_id == "LOG001")

    s = SensorReading(**SensorReading.model_config["json_schema_extra"]["example"])
    check("SensorReading model works", s.reading_id == "SENSOR001")

    h = Heuristic(**Heuristic.model_config["json_schema_extra"]["example"])
    check("Heuristic model works", len(h.conditions) == 2)

    v = ValidationResult(**ValidationResult.model_config["json_schema_extra"]["example"])
    check("ValidationResult model works", v.decision == "Accepted")

    r = OperationalRule(**OperationalRule.model_config["json_schema_extra"]["example"])
    check("OperationalRule model works", r.rule_id == "RULE001")

    t = InterviewTranscript(**InterviewTranscript.model_config["json_schema_extra"]["example"])
    check("InterviewTranscript model works", t.interview_id == "INT001")


def test_synthetic_data_generation() -> tuple:
    section("Testing synthetic data generation...")

    generator = SyntheticDataGenerator(data_dir=TEST_DATA_DIR)

    employees = generator.generate_employees()
    check(f"Generated {len(employees)} employees", len(employees) == 3)

    logs = generator.generate_maintenance_logs()
    bearing_count = sum(1 for l in logs if l["failure_type"] == "bearing_failure")
    other_count = len(logs) - bearing_count
    check(
        f"Generated {len(logs)} maintenance logs ({bearing_count} bearing failures)",
        len(logs) == 92 and bearing_count >= 30 and other_count >= 60,
    )

    readings = generator.generate_sensor_history(logs)
    high_pattern_count = sum(
        1 for r in readings if r["humidity_percent"] > 80 and r["vibration_mm_s"] > 2.0
    )
    check(
        f"Generated {len(readings)} sensor readings ({high_pattern_count} high humidity)",
        len(readings) == 500,
    )

    transcripts = generator.generate_interview_transcripts()
    check(f"Generated {len(transcripts)} interview transcripts", len(transcripts) == 3)

    # The statistical claim that actually matters: is the embedded pattern
    # real, i.e. does it show up as a strong, significant correlation
    # between "pattern present near incident" and "incident is a bearing
    # failure"? This is what Phase 4's ValidationEngine will test later.
    section("Testing embedded pattern strength...")

    def nearest_reading(log, readings, window_hours=24):
        same_machine = [r for r in readings if r["machine_id"] == log["machine_id"]]
        candidates = [
            r
            for r in same_machine
            if abs((r["_timestamp_dt"] - log["_timestamp_dt"]).total_seconds())
            <= window_hours * 3600
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda r: abs((r["_timestamp_dt"] - log["_timestamp_dt"]).total_seconds()),
        )

    a = b = c = d = 0  # pattern&bearing, pattern&other, nopattern&bearing, nopattern&other
    for log in logs:
        r = nearest_reading(log, readings)
        if r is None:
            continue
        is_bearing = log["failure_type"] == "bearing_failure"
        pattern = r["humidity_percent"] > 80 and r["vibration_mm_s"] > 2.0
        if is_bearing and pattern:
            a += 1
        elif is_bearing and not pattern:
            c += 1
        elif (not is_bearing) and pattern:
            b += 1
        else:
            d += 1

    table = np.array([[a, b], [c, d]])
    chi2, p_value, _, _ = stats.chi2_contingency(table)
    p_bearing = a / (a + c) if (a + c) else 0.0
    p_other = b / (b + d) if (b + d) else 0.0

    check(
        f"Pattern present near bearing failures ({p_bearing*100:.1f}%) "
        f"exceeds other failures ({p_other*100:.1f}%)",
        p_bearing > p_other,
    )
    check(
        f"Chi-square test is significant (chi2={chi2:.2f}, p={p_value:.6f})",
        p_value < 0.05,
    )

    return employees, logs, readings, transcripts


def test_interview_queue(employees: list) -> None:
    section("Testing interview queue generation...")

    employee_models = [
        Employee(
            employee_id=e["employee_id"],
            name=e["name"],
            machine_id=e["machine_id"],
            years_experience=e["years_experience"],
            retirement_date=e["retirement_date"],
            expertise_areas=e["expertise_areas"].split(","),
            interview_completed=e["interview_completed"],
        )
        for e in employees
    ]

    generator = InterviewQueueGenerator(config_dir=TEST_CONFIG_DIR)
    queue = generator.generate(employee_models)

    check(f"Generated interview queue with {len(queue)} employees", len(queue) == 3)
    for entry in queue:
        print(f"  {entry['queue_position']}. {entry['name']} ({entry['years_experience']} years)")

    check(
        "Queue ordered by experience (descending)",
        [q["years_experience"] for q in queue] == sorted(
            (q["years_experience"] for q in queue), reverse=True
        ),
    )


def test_database_initialization() -> None:
    section("Testing database initialization...")

    db = Database(db_path=TEST_DB_PATH)
    db.connect()
    db.init_schema()

    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {row["name"] for row in tables}
    expected_tables = {
        "employees",
        "maintenance_logs",
        "sensor_readings",
        "heuristics",
        "validation_results",
        "operational_rules",
        "interview_transcripts",
    }
    check(
        f"Database initialized with {len(table_names)} tables",
        expected_tables.issubset(table_names),
    )
    db.close()


def test_csv_and_json_generation(employees, logs, readings, transcripts) -> None:
    section("Testing CSV file generation...")

    generator = SyntheticDataGenerator(data_dir=TEST_DATA_DIR)
    generator.save_employees_csv(employees)
    generator.save_maintenance_logs_csv(logs)
    generator.save_sensor_history_csv(readings)

    data_dir = Path(TEST_DATA_DIR)

    with open(data_dir / "employees.csv") as f:
        row_count = sum(1 for _ in f) - 1
    check(f"employees.csv: {row_count} rows", row_count == 3)

    with open(data_dir / "maintenance_logs.csv") as f:
        row_count = sum(1 for _ in f) - 1
    check(f"maintenance_logs.csv: {row_count} rows", row_count == 92)

    with open(data_dir / "sensor_history.csv") as f:
        row_count = sum(1 for _ in f) - 1
    check(f"sensor_history.csv: {row_count} rows", row_count == 500)

    section("Testing JSON file generation...")
    generator.save_interview_transcripts_json(transcripts)
    with open(data_dir / "interview_transcripts.json") as f:
        loaded = json.load(f)
    check(f"interview_transcripts.json: {len(loaded)} transcripts", len(loaded) == 3)


def cleanup() -> None:
    for path in (TEST_DATA_DIR, TEST_CONFIG_DIR):
        shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("CONTINUUM Phase 1 Test Suite")
    print("=" * 60)

    try:
        test_models()
        employees, logs, readings, transcripts = test_synthetic_data_generation()
        test_interview_queue(employees)
        test_database_initialization()
        test_csv_and_json_generation(employees, logs, readings, transcripts)
    except AssertionError as exc:
        print("\n" + "=" * 60)
        print(f"{FAIL} Phase 1 tests FAILED: {exc}")
        print("=" * 60)
        return 1
    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"{PASS} All Phase 1 tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())