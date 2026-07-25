"""
main.py

CONTINUUM entrypoint for Phase 1 initialization.

Running this module:
  1. Configures logging
  2. Initializes the SQLite database (creates the schema if needed)
  3. Generates synthetic datasets (employees, maintenance logs, sensor
     readings, interview transcripts) and writes them to data/
  4. Loads that data into the database
  5. Builds and persists the interview queue to config/interview_queue.json

This is Phase 1 only. From Phase 2 onward, the real interface becomes
the MCP server (see mcp/server.py) — this file stays as the one-shot
"set the system up" entrypoint, not the ongoing interface.
"""

import logging

from database.sqlite import Database
from models.employee import Employee
from models.maintenance import MaintenanceLog, SensorReading
from utils.interview_queue import InterviewQueueGenerator
from utils.logger import configure_logging
from utils.synthetic_data import SyntheticDataGenerator

logger = logging.getLogger(__name__)

DATA_DIR = "data"
CONFIG_DIR = "config"
DB_PATH = f"{DATA_DIR}/continuum.db"


def _employee_dict_to_model(raw: dict) -> Employee:
    """Convert a raw employee dict (as produced by SyntheticDataGenerator)
    into an Employee model instance."""
    return Employee(
        employee_id=raw["employee_id"],
        name=raw["name"],
        machine_id=raw["machine_id"],
        years_experience=raw["years_experience"],
        retirement_date=raw["retirement_date"],
        expertise_areas=raw["expertise_areas"].split(","),
        interview_completed=raw["interview_completed"],
    )


def _log_dict_to_model(raw: dict) -> MaintenanceLog:
    """Convert a raw maintenance log dict into a MaintenanceLog model instance."""
    return MaintenanceLog(
        log_id=raw["log_id"],
        machine_id=raw["machine_id"],
        component=raw["component"],
        failure_type=raw["failure_type"],
        timestamp=raw["timestamp"],
        description=raw["description"],
        technician_id=raw["technician_id"],
        resolution=raw["resolution"],
    )


def _reading_dict_to_model(raw: dict) -> SensorReading:
    """Convert a raw sensor reading dict into a SensorReading model instance."""
    return SensorReading(
        reading_id=raw["reading_id"],
        machine_id=raw["machine_id"],
        timestamp=raw["timestamp"],
        humidity_percent=raw["humidity_percent"],
        vibration_mm_s=raw["vibration_mm_s"],
        temperature_celsius=raw["temperature_celsius"],
        pressure_bar=raw["pressure_bar"],
    )


def initialize() -> None:
    """Run full Phase 1 initialization: DB schema, synthetic data, interview queue."""
    logger.info("Starting CONTINUUM Phase 1 initialization")

    # 1. Database schema
    db = Database(db_path=DB_PATH)
    db.connect()
    db.init_schema()
    logger.info("Database schema ready")

    # 2. Synthetic data generation (writes CSVs/JSON to data/)
    data_gen = SyntheticDataGenerator(data_dir=DATA_DIR)
    employees_raw = data_gen.generate_employees()
    logs_raw = data_gen.generate_maintenance_logs()
    readings_raw = data_gen.generate_sensor_history(logs_raw)
    transcripts_raw = data_gen.generate_interview_transcripts()

    data_gen.save_employees_csv(employees_raw)
    data_gen.save_maintenance_logs_csv(logs_raw)
    data_gen.save_sensor_history_csv(readings_raw)
    data_gen.save_interview_transcripts_json(transcripts_raw)
    logger.info("Synthetic datasets generated")

    # 3. Load synthetic data into the database
    employees = [_employee_dict_to_model(e) for e in employees_raw]
    for employee in employees:
        db.insert_employee(employee)

    for raw_log in logs_raw:
        db.insert_maintenance_log(_log_dict_to_model(raw_log))

    for raw_reading in readings_raw:
        db.insert_sensor_reading(_reading_dict_to_model(raw_reading))

    logger.info(
        "Loaded %d employees, %d maintenance logs, %d sensor readings into the database",
        len(employees), len(logs_raw), len(readings_raw),
    )

    # 4. Interview queue
    queue_gen = InterviewQueueGenerator(config_dir=CONFIG_DIR)
    queue = queue_gen.generate(employees)
    logger.info("Interview queue generated with %d entries", len(queue))

    db.close()
    logger.info("CONTINUUM Phase 1 initialization complete")


def main() -> None:
    configure_logging()
    initialize()


if __name__ == "__main__":
    main()