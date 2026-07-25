"""SQLite database module for CONTINUUM."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from models.employee import Employee
from models.heuristic import Heuristic, HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from models.operational_rule import InterviewTranscript, OperationalRule
from models.validation import ValidationResult

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for CONTINUUM."""

    def __init__(self, db_path: str = "data/continuum.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        """Connect to database."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Cursor object
        """
        if not self.connection:
            self.connect()
        return self.connection.execute(query, params)

    def executemany(self, query: str, params: list) -> None:
        """Execute multiple queries.

        Args:
            query: SQL query
            params: List of parameter tuples
        """
        if not self.connection:
            self.connect()
        self.connection.executemany(query, params)
        self.connection.commit()

    def commit(self) -> None:
        """Commit transaction."""
        if self.connection:
            self.connection.commit()

    def init_schema(self) -> None:
        """Initialize database schema."""
        if not self.connection:
            self.connect()

        # Employees table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                years_experience INTEGER NOT NULL,
                retirement_date TEXT NOT NULL,
                expertise_areas TEXT,
                interview_completed BOOLEAN DEFAULT 0
            )
            """
        )

        # Maintenance logs table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                log_id TEXT PRIMARY KEY,
                machine_id TEXT NOT NULL,
                component TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT,
                technician_id TEXT,
                resolution TEXT,
                FOREIGN KEY (technician_id) REFERENCES employees(employee_id)
            )
            """
        )

        # Sensor readings table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                reading_id TEXT PRIMARY KEY,
                machine_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                humidity_percent REAL NOT NULL,
                vibration_mm_s REAL NOT NULL,
                temperature_celsius REAL NOT NULL,
                pressure_bar REAL NOT NULL
            )
            """
        )

        # Heuristics table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS heuristics (
                heuristic_id TEXT PRIMARY KEY,
                machine_id TEXT NOT NULL,
                component TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                trigger TEXT NOT NULL,
                conditions TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                recommended_action TEXT,
                expert_confidence REAL,
                extracted_from_interview TEXT,
                extraction_timestamp TEXT
            )
            """
        )

        # Validation results table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_results (
                validation_id TEXT PRIMARY KEY,
                heuristic_id TEXT NOT NULL,
                support_count INTEGER,
                total_occurrences INTEGER,
                conditional_probability REAL,
                pearson_correlation REAL,
                chi_square_statistic REAL,
                chi_square_p_value REAL,
                confidence_score REAL,
                decision TEXT,
                reasoning TEXT,
                validation_timestamp TEXT,
                FOREIGN KEY (heuristic_id) REFERENCES heuristics(heuristic_id)
            )
            """
        )

        # Operational rules table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS operational_rules (
                rule_id TEXT PRIMARY KEY,
                heuristic_id TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                component TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                trigger TEXT NOT NULL,
                conditions TEXT NOT NULL,
                recommended_action TEXT,
                confidence_score REAL,
                created_timestamp TEXT,
                FOREIGN KEY (heuristic_id) REFERENCES heuristics(heuristic_id)
            )
            """
        )

        # Interview transcripts table
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_transcripts (
                interview_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                incident_id TEXT,
                transcript TEXT,
                timestamp TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
            """
        )

        self.commit()
        logger.info("Database schema initialized")

    def close(self) -> None:
        """Close database connection."""
        self.disconnect()

    # ------------------------------------------------------------------
    # Employees
    # ------------------------------------------------------------------

    def insert_employee(self, employee: Employee) -> None:
        """Insert a single Employee record."""
        self.execute(
            """
            INSERT INTO employees
                (employee_id, name, machine_id, years_experience,
                 retirement_date, expertise_areas, interview_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee.employee_id,
                employee.name,
                employee.machine_id,
                employee.years_experience,
                employee.retirement_date.isoformat(),
                json.dumps(employee.expertise_areas),
                int(employee.interview_completed),
            ),
        )
        self.commit()

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Fetch a single Employee by ID, or None if not found."""
        row = self.execute(
            "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
        ).fetchone()
        return self._row_to_employee(row) if row else None

    def get_all_employees(self) -> List[Employee]:
        """Fetch every Employee, ordered by years_experience desc, retirement_date asc."""
        rows = self.execute(
            "SELECT * FROM employees ORDER BY years_experience DESC, retirement_date ASC"
        ).fetchall()
        return [self._row_to_employee(row) for row in rows]

    @staticmethod
    def _row_to_employee(row: sqlite3.Row) -> Employee:
        return Employee(
            employee_id=row["employee_id"],
            name=row["name"],
            machine_id=row["machine_id"],
            years_experience=row["years_experience"],
            retirement_date=row["retirement_date"],
            expertise_areas=json.loads(row["expertise_areas"] or "[]"),
            interview_completed=bool(row["interview_completed"]),
        )

    # ------------------------------------------------------------------
    # Maintenance logs
    # ------------------------------------------------------------------

    def insert_maintenance_log(self, log: MaintenanceLog) -> None:
        """Insert a single MaintenanceLog record."""
        self.execute(
            """
            INSERT INTO maintenance_logs
                (log_id, machine_id, component, failure_type, timestamp,
                 description, technician_id, resolution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.log_id,
                log.machine_id,
                log.component,
                log.failure_type,
                log.timestamp.isoformat(),
                log.description,
                log.technician_id,
                log.resolution,
            ),
        )
        self.commit()

    def get_maintenance_logs(self, machine_id: Optional[str] = None) -> List[MaintenanceLog]:
        """Fetch maintenance logs, optionally filtered by machine_id."""
        if machine_id:
            rows = self.execute(
                "SELECT * FROM maintenance_logs WHERE machine_id = ?", (machine_id,)
            ).fetchall()
        else:
            rows = self.execute("SELECT * FROM maintenance_logs").fetchall()
        return [self._row_to_maintenance_log(row) for row in rows]

    @staticmethod
    def _row_to_maintenance_log(row: sqlite3.Row) -> MaintenanceLog:
        return MaintenanceLog(
            log_id=row["log_id"],
            machine_id=row["machine_id"],
            component=row["component"],
            failure_type=row["failure_type"],
            timestamp=row["timestamp"],
            description=row["description"],
            technician_id=row["technician_id"],
            resolution=row["resolution"],
        )

    # ------------------------------------------------------------------
    # Sensor readings
    # ------------------------------------------------------------------

    def insert_sensor_reading(self, reading: SensorReading) -> None:
        """Insert a single SensorReading record."""
        self.execute(
            """
            INSERT INTO sensor_readings
                (reading_id, machine_id, timestamp, humidity_percent,
                 vibration_mm_s, temperature_celsius, pressure_bar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reading.reading_id,
                reading.machine_id,
                reading.timestamp.isoformat(),
                reading.humidity_percent,
                reading.vibration_mm_s,
                reading.temperature_celsius,
                reading.pressure_bar,
            ),
        )
        self.commit()

    def get_sensor_readings(self, machine_id: Optional[str] = None) -> List[SensorReading]:
        """Fetch sensor readings, optionally filtered by machine_id."""
        if machine_id:
            rows = self.execute(
                "SELECT * FROM sensor_readings WHERE machine_id = ?", (machine_id,)
            ).fetchall()
        else:
            rows = self.execute("SELECT * FROM sensor_readings").fetchall()
        return [self._row_to_sensor_reading(row) for row in rows]

    @staticmethod
    def _row_to_sensor_reading(row: sqlite3.Row) -> SensorReading:
        return SensorReading(
            reading_id=row["reading_id"],
            machine_id=row["machine_id"],
            timestamp=row["timestamp"],
            humidity_percent=row["humidity_percent"],
            vibration_mm_s=row["vibration_mm_s"],
            temperature_celsius=row["temperature_celsius"],
            pressure_bar=row["pressure_bar"],
        )

    # ------------------------------------------------------------------
    # Heuristics
    # ------------------------------------------------------------------

    def insert_heuristic(self, heuristic: Heuristic) -> None:
        """Insert a single Heuristic record."""
        self.execute(
            """
            INSERT INTO heuristics
                (heuristic_id, machine_id, component, failure_type, trigger,
                 conditions, symptoms, recommended_action, expert_confidence,
                 extracted_from_interview, extraction_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                heuristic.heuristic_id,
                heuristic.machine_id,
                heuristic.component,
                heuristic.failure_type,
                heuristic.trigger,
                json.dumps([c.model_dump() for c in heuristic.conditions]),
                json.dumps(heuristic.symptoms),
                heuristic.recommended_action,
                heuristic.expert_confidence,
                heuristic.extracted_from_interview,
                heuristic.extraction_timestamp.isoformat(),
            ),
        )
        self.commit()

    def get_heuristic(self, heuristic_id: str) -> Optional[Heuristic]:
        """Fetch a single Heuristic by ID, or None if not found."""
        row = self.execute(
            "SELECT * FROM heuristics WHERE heuristic_id = ?", (heuristic_id,)
        ).fetchone()
        return self._row_to_heuristic(row) if row else None

    def get_all_heuristics(self) -> List[Heuristic]:
        """Fetch every Heuristic."""
        rows = self.execute("SELECT * FROM heuristics").fetchall()
        return [self._row_to_heuristic(row) for row in rows]

    @staticmethod
    def _row_to_heuristic(row: sqlite3.Row) -> Heuristic:
        return Heuristic(
            heuristic_id=row["heuristic_id"],
            machine_id=row["machine_id"],
            component=row["component"],
            failure_type=row["failure_type"],
            trigger=row["trigger"],
            conditions=[
                HeuristicCondition(**c) for c in json.loads(row["conditions"])
            ],
            symptoms=json.loads(row["symptoms"] or "[]"),
            recommended_action=row["recommended_action"],
            expert_confidence=row["expert_confidence"],
            extracted_from_interview=row["extracted_from_interview"],
            extraction_timestamp=row["extraction_timestamp"],
        )

    # ------------------------------------------------------------------
    # Validation results
    # ------------------------------------------------------------------

    def insert_validation_result(self, result: ValidationResult) -> None:
        """Insert a single ValidationResult record."""
        self.execute(
            """
            INSERT INTO validation_results
                (validation_id, heuristic_id, support_count, total_occurrences,
                 conditional_probability, pearson_correlation, chi_square_statistic,
                 chi_square_p_value, confidence_score, decision, reasoning,
                 validation_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.validation_id,
                result.heuristic_id,
                result.support_count,
                result.total_occurrences,
                result.conditional_probability,
                result.pearson_correlation,
                result.chi_square_statistic,
                result.chi_square_p_value,
                result.confidence_score,
                result.decision,
                result.reasoning,
                result.validation_timestamp.isoformat(),
            ),
        )
        self.commit()

    def get_validation_result(self, heuristic_id: str) -> Optional[ValidationResult]:
        """Fetch the ValidationResult for a given heuristic_id, or None."""
        row = self.execute(
            "SELECT * FROM validation_results WHERE heuristic_id = ?", (heuristic_id,)
        ).fetchone()
        return self._row_to_validation_result(row) if row else None

    @staticmethod
    def _row_to_validation_result(row: sqlite3.Row) -> ValidationResult:
        return ValidationResult(
            validation_id=row["validation_id"],
            heuristic_id=row["heuristic_id"],
            support_count=row["support_count"],
            total_occurrences=row["total_occurrences"],
            conditional_probability=row["conditional_probability"],
            pearson_correlation=row["pearson_correlation"],
            chi_square_statistic=row["chi_square_statistic"],
            chi_square_p_value=row["chi_square_p_value"],
            confidence_score=row["confidence_score"],
            decision=row["decision"],
            reasoning=row["reasoning"],
            validation_timestamp=row["validation_timestamp"],
        )

    # ------------------------------------------------------------------
    # Operational rules
    # ------------------------------------------------------------------

    def is_duplicate_rule(self, rule: OperationalRule) -> bool:
        """Check whether an equivalent rule already exists.

        Duplicate = same machine_id, failure_type, trigger, and condition set.
        """
        rows = self.execute(
            """
            SELECT conditions FROM operational_rules
            WHERE machine_id = ? AND failure_type = ? AND trigger = ?
            """,
            (rule.machine_id, rule.failure_type, rule.trigger),
        ).fetchall()

        target_key = rule.duplicate_key()
        for row in rows:
            existing_conditions = [
                HeuristicCondition(**c) for c in json.loads(row["conditions"])
            ]
            existing_key = (
                rule.machine_id,
                rule.failure_type,
                rule.trigger,
                tuple(sorted((c.parameter, c.operator, c.value) for c in existing_conditions)),
            )
            if existing_key == target_key:
                return True
        return False

    def insert_operational_rule(self, rule: OperationalRule) -> bool:
        """Insert an OperationalRule if it isn't a duplicate.

        Returns:
            True if inserted, False if skipped as a duplicate.
        """
        if self.is_duplicate_rule(rule):
            logger.info(f"Skipping duplicate operational rule: {rule.rule_id}")
            return False

        self.execute(
            """
            INSERT INTO operational_rules
                (rule_id, heuristic_id, machine_id, component, failure_type,
                 trigger, conditions, recommended_action, confidence_score,
                 created_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule.rule_id,
                rule.heuristic_id,
                rule.machine_id,
                rule.component,
                rule.failure_type,
                rule.trigger,
                json.dumps([c.model_dump() for c in rule.conditions]),
                rule.recommended_action,
                rule.confidence_score,
                rule.created_timestamp.isoformat(),
            ),
        )
        self.commit()
        return True

    def get_operational_rules(self, machine_id: Optional[str] = None) -> List[OperationalRule]:
        """Fetch operational rules, optionally filtered by machine_id."""
        if machine_id:
            rows = self.execute(
                "SELECT * FROM operational_rules WHERE machine_id = ?", (machine_id,)
            ).fetchall()
        else:
            rows = self.execute("SELECT * FROM operational_rules").fetchall()
        return [self._row_to_operational_rule(row) for row in rows]

    @staticmethod
    def _row_to_operational_rule(row: sqlite3.Row) -> OperationalRule:
        return OperationalRule(
            rule_id=row["rule_id"],
            heuristic_id=row["heuristic_id"],
            machine_id=row["machine_id"],
            component=row["component"],
            failure_type=row["failure_type"],
            trigger=row["trigger"],
            conditions=[
                HeuristicCondition(**c) for c in json.loads(row["conditions"])
            ],
            recommended_action=row["recommended_action"],
            confidence_score=row["confidence_score"],
            created_timestamp=row["created_timestamp"],
        )

    # ------------------------------------------------------------------
    # Interview transcripts
    # ------------------------------------------------------------------

    def insert_interview_transcript(self, transcript: InterviewTranscript) -> None:
        """Insert a single InterviewTranscript record."""
        self.execute(
            """
            INSERT INTO interview_transcripts
                (interview_id, employee_id, incident_id, transcript, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                transcript.interview_id,
                transcript.employee_id,
                transcript.incident_id,
                transcript.transcript,
                transcript.timestamp.isoformat(),
            ),
        )
        self.commit()

    def get_interview_transcript(self, interview_id: str) -> Optional[InterviewTranscript]:
        """Fetch a single InterviewTranscript by ID, or None if not found."""
        row = self.execute(
            "SELECT * FROM interview_transcripts WHERE interview_id = ?", (interview_id,)
        ).fetchone()
        return self._row_to_interview_transcript(row) if row else None

    @staticmethod
    def _row_to_interview_transcript(row: sqlite3.Row) -> InterviewTranscript:
        return InterviewTranscript(
            interview_id=row["interview_id"],
            employee_id=row["employee_id"],
            incident_id=row["incident_id"],
            transcript=row["transcript"],
            timestamp=row["timestamp"],
        )