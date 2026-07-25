"""PostgreSQL / Neon database module for CONTINUUM."""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from dotenv import load_dotenv

from models.employee import Employee
from models.heuristic import Heuristic, HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from models.operational_rule import InterviewTranscript, OperationalRule
from models.validation import ValidationResult

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class PostgresDatabase:
    """PostgreSQL / Neon database manager for CONTINUUM."""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize database connection string.

        Args:
            db_url: PostgreSQL connection URL. Defaults to DATABASE_URL or NEON_DATABASE_URL env var.
        """
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is required for PostgreSQL connections. Install via pip install psycopg2-binary")
        
        self.db_url = db_url or os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
        if not self.db_url:
            raise ValueError("No database URL provided and neither DATABASE_URL nor NEON_DATABASE_URL is set in environment")
        
        self.connection = None

    def __enter__(self) -> "PostgresDatabase":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        """Connect to Neon PostgreSQL database."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.db_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.info("Connected to Neon PostgreSQL database")

    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Disconnected from Neon PostgreSQL database")

    def close(self) -> None:
        """Close database connection."""
        self.disconnect()

    def execute(self, query: str, params: tuple = ()):
        """Execute a SQL query.

        Args:
            query: SQL query string (uses %s placeholders)
            params: Query parameters tuple

        Returns:
            Cursor object
        """
        if not self.connection or self.connection.closed:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor

    def executemany(self, query: str, params: list) -> None:
        """Execute multiple SQL queries.

        Args:
            query: SQL query
            params: List of parameter tuples
        """
        if not self.connection or self.connection.closed:
            self.connect()
        cursor = self.connection.cursor()
        cursor.executemany(query, params)
        self.connection.commit()

    def commit(self) -> None:
        """Commit transaction."""
        if self.connection and not self.connection.closed:
            self.connection.commit()

    def init_schema(self) -> None:
        """Initialize database schema on Neon PostgreSQL."""
        if not self.connection or self.connection.closed:
            self.connect()

        with self.connection.cursor() as cursor:
            # Employees table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    years_experience INTEGER NOT NULL,
                    retirement_date TEXT NOT NULL,
                    expertise_areas TEXT,
                    interview_completed BOOLEAN DEFAULT FALSE
                );
                """
            )

            # Maintenance logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    log_id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    technician_id TEXT REFERENCES employees(employee_id),
                    resolution TEXT
                );
                """
            )

            # Sensor readings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    reading_id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    humidity_percent DOUBLE PRECISION NOT NULL,
                    vibration_mm_s DOUBLE PRECISION NOT NULL,
                    temperature_celsius DOUBLE PRECISION NOT NULL,
                    pressure_bar DOUBLE PRECISION NOT NULL
                );
                """
            )

            # Heuristics table
            cursor.execute(
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
                    expert_confidence DOUBLE PRECISION,
                    extracted_from_interview TEXT,
                    extraction_timestamp TEXT
                );
                """
            )

            # Validation results table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_results (
                    validation_id TEXT PRIMARY KEY,
                    heuristic_id TEXT NOT NULL REFERENCES heuristics(heuristic_id),
                    support_count INTEGER,
                    total_occurrences INTEGER,
                    conditional_probability DOUBLE PRECISION,
                    pearson_correlation DOUBLE PRECISION,
                    chi_square_statistic DOUBLE PRECISION,
                    chi_square_p_value DOUBLE PRECISION,
                    confidence_score DOUBLE PRECISION,
                    decision TEXT,
                    reasoning TEXT,
                    validation_timestamp TEXT
                );
                """
            )

            # Operational rules table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_rules (
                    rule_id TEXT PRIMARY KEY,
                    heuristic_id TEXT NOT NULL REFERENCES heuristics(heuristic_id),
                    machine_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    recommended_action TEXT,
                    confidence_score DOUBLE PRECISION,
                    created_timestamp TEXT
                );
                """
            )

            # Interview transcripts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_transcripts (
                    interview_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
                    incident_id TEXT,
                    transcript TEXT,
                    timestamp TEXT
                );
                """
            )

        self.commit()
        logger.info("Neon PostgreSQL database schema initialized")

    # ------------------------------------------------------------------
    # Employees
    # ------------------------------------------------------------------

    def insert_employee(self, employee: Employee) -> None:
        """Insert a single Employee record."""
        cursor = self.execute(
            """
            INSERT INTO employees
                (employee_id, name, machine_id, years_experience,
                 retirement_date, expertise_areas, interview_completed)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (employee_id) DO UPDATE SET
                name = EXCLUDED.name,
                machine_id = EXCLUDED.machine_id,
                years_experience = EXCLUDED.years_experience,
                retirement_date = EXCLUDED.retirement_date,
                expertise_areas = EXCLUDED.expertise_areas,
                interview_completed = EXCLUDED.interview_completed
            """,
            (
                employee.employee_id,
                employee.name,
                employee.machine_id,
                employee.years_experience,
                employee.retirement_date.isoformat(),
                json.dumps(employee.expertise_areas),
                employee.interview_completed,
            ),
        )
        self.commit()

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Fetch a single Employee by ID, or None if not found."""
        cursor = self.execute(
            "SELECT * FROM employees WHERE employee_id = %s", (employee_id,)
        )
        row = cursor.fetchone()
        return self._row_to_employee(row) if row else None

    def get_all_employees(self) -> List[Employee]:
        """Fetch every Employee, ordered by years_experience desc, retirement_date asc."""
        cursor = self.execute(
            "SELECT * FROM employees ORDER BY years_experience DESC, retirement_date ASC"
        )
        rows = cursor.fetchall()
        return [self._row_to_employee(row) for row in rows]

    @staticmethod
    def _row_to_employee(row: dict) -> Employee:
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (log_id) DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                component = EXCLUDED.component,
                failure_type = EXCLUDED.failure_type,
                timestamp = EXCLUDED.timestamp,
                description = EXCLUDED.description,
                technician_id = EXCLUDED.technician_id,
                resolution = EXCLUDED.resolution
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

    def insert_maintenance_logs_batch(self, logs: List[MaintenanceLog]) -> None:
        """Insert multiple MaintenanceLog records efficiently in bulk."""
        if not logs:
            return
        if not self.connection or self.connection.closed:
            self.connect()
        query = """
            INSERT INTO maintenance_logs
                (log_id, machine_id, component, failure_type, timestamp,
                 description, technician_id, resolution)
            VALUES %s
            ON CONFLICT (log_id) DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                component = EXCLUDED.component,
                failure_type = EXCLUDED.failure_type,
                timestamp = EXCLUDED.timestamp,
                description = EXCLUDED.description,
                technician_id = EXCLUDED.technician_id,
                resolution = EXCLUDED.resolution
        """
        argslist = [
            (
                log.log_id,
                log.machine_id,
                log.component,
                log.failure_type,
                log.timestamp.isoformat(),
                log.description,
                log.technician_id,
                log.resolution,
            )
            for log in logs
        ]
        with self.connection.cursor() as cursor:
            psycopg2.extras.execute_values(cursor, query, argslist, page_size=1000)
        self.commit()

    def get_maintenance_logs(self, machine_id: Optional[str] = None) -> List[MaintenanceLog]:
        """Fetch maintenance logs, optionally filtered by machine_id."""
        if machine_id:
            cursor = self.execute(
                "SELECT * FROM maintenance_logs WHERE machine_id = %s", (machine_id,)
            )
        else:
            cursor = self.execute("SELECT * FROM maintenance_logs")
        rows = cursor.fetchall()
        return [self._row_to_maintenance_log(row) for row in rows]

    @staticmethod
    def _row_to_maintenance_log(row: dict) -> MaintenanceLog:
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (reading_id) DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                timestamp = EXCLUDED.timestamp,
                humidity_percent = EXCLUDED.humidity_percent,
                vibration_mm_s = EXCLUDED.vibration_mm_s,
                temperature_celsius = EXCLUDED.temperature_celsius,
                pressure_bar = EXCLUDED.pressure_bar
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

    def insert_sensor_readings_batch(self, readings: List[SensorReading]) -> None:
        """Insert multiple SensorReading records efficiently in bulk."""
        if not readings:
            return
        if not self.connection or self.connection.closed:
            self.connect()
        query = """
            INSERT INTO sensor_readings
                (reading_id, machine_id, timestamp, humidity_percent,
                 vibration_mm_s, temperature_celsius, pressure_bar)
            VALUES %s
            ON CONFLICT (reading_id) DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                timestamp = EXCLUDED.timestamp,
                humidity_percent = EXCLUDED.humidity_percent,
                vibration_mm_s = EXCLUDED.vibration_mm_s,
                temperature_celsius = EXCLUDED.temperature_celsius,
                pressure_bar = EXCLUDED.pressure_bar
        """
        argslist = [
            (
                r.reading_id,
                r.machine_id,
                r.timestamp.isoformat(),
                r.humidity_percent,
                r.vibration_mm_s,
                r.temperature_celsius,
                r.pressure_bar,
            )
            for r in readings
        ]
        with self.connection.cursor() as cursor:
            psycopg2.extras.execute_values(cursor, query, argslist, page_size=1000)
        self.commit()


    def get_sensor_readings(self, machine_id: Optional[str] = None) -> List[SensorReading]:
        """Fetch sensor readings, optionally filtered by machine_id."""
        if machine_id:
            cursor = self.execute(
                "SELECT * FROM sensor_readings WHERE machine_id = %s", (machine_id,)
            )
        else:
            cursor = self.execute("SELECT * FROM sensor_readings")
        rows = cursor.fetchall()
        return [self._row_to_sensor_reading(row) for row in rows]

    @staticmethod
    def _row_to_sensor_reading(row: dict) -> SensorReading:
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (heuristic_id) DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                component = EXCLUDED.component,
                failure_type = EXCLUDED.failure_type,
                trigger = EXCLUDED.trigger,
                conditions = EXCLUDED.conditions,
                symptoms = EXCLUDED.symptoms,
                recommended_action = EXCLUDED.recommended_action,
                expert_confidence = EXCLUDED.expert_confidence,
                extracted_from_interview = EXCLUDED.extracted_from_interview,
                extraction_timestamp = EXCLUDED.extraction_timestamp
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
        cursor = self.execute(
            "SELECT * FROM heuristics WHERE heuristic_id = %s", (heuristic_id,)
        )
        row = cursor.fetchone()
        return self._row_to_heuristic(row) if row else None

    def get_all_heuristics(self) -> List[Heuristic]:
        """Fetch every Heuristic."""
        cursor = self.execute("SELECT * FROM heuristics")
        rows = cursor.fetchall()
        return [self._row_to_heuristic(row) for row in rows]

    @staticmethod
    def _row_to_heuristic(row: dict) -> Heuristic:
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (validation_id) DO UPDATE SET
                heuristic_id = EXCLUDED.heuristic_id,
                support_count = EXCLUDED.support_count,
                total_occurrences = EXCLUDED.total_occurrences,
                conditional_probability = EXCLUDED.conditional_probability,
                pearson_correlation = EXCLUDED.pearson_correlation,
                chi_square_statistic = EXCLUDED.chi_square_statistic,
                chi_square_p_value = EXCLUDED.chi_square_p_value,
                confidence_score = EXCLUDED.confidence_score,
                decision = EXCLUDED.decision,
                reasoning = EXCLUDED.reasoning,
                validation_timestamp = EXCLUDED.validation_timestamp
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
        cursor = self.execute(
            "SELECT * FROM validation_results WHERE heuristic_id = %s", (heuristic_id,)
        )
        row = cursor.fetchone()
        return self._row_to_validation_result(row) if row else None

    @staticmethod
    def _row_to_validation_result(row: dict) -> ValidationResult:
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
        """Check whether an equivalent rule already exists."""
        cursor = self.execute(
            """
            SELECT conditions FROM operational_rules
            WHERE machine_id = %s AND failure_type = %s AND trigger = %s
            """,
            (rule.machine_id, rule.failure_type, rule.trigger),
        )
        rows = cursor.fetchall()

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
        """Insert an OperationalRule if it isn't a duplicate."""
        if self.is_duplicate_rule(rule):
            logger.info(f"Skipping duplicate operational rule: {rule.rule_id}")
            return False

        self.execute(
            """
            INSERT INTO operational_rules
                (rule_id, heuristic_id, machine_id, component, failure_type,
                 trigger, conditions, recommended_action, confidence_score,
                 created_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rule_id) DO UPDATE SET
                heuristic_id = EXCLUDED.heuristic_id,
                machine_id = EXCLUDED.machine_id,
                component = EXCLUDED.component,
                failure_type = EXCLUDED.failure_type,
                trigger = EXCLUDED.trigger,
                conditions = EXCLUDED.conditions,
                recommended_action = EXCLUDED.recommended_action,
                confidence_score = EXCLUDED.confidence_score,
                created_timestamp = EXCLUDED.created_timestamp
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
            cursor = self.execute(
                "SELECT * FROM operational_rules WHERE machine_id = %s", (machine_id,)
            )
        else:
            cursor = self.execute("SELECT * FROM operational_rules")
        rows = cursor.fetchall()
        return [self._row_to_operational_rule(row) for row in rows]

    @staticmethod
    def _row_to_operational_rule(row: dict) -> OperationalRule:
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
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (interview_id) DO UPDATE SET
                employee_id = EXCLUDED.employee_id,
                incident_id = EXCLUDED.incident_id,
                transcript = EXCLUDED.transcript,
                timestamp = EXCLUDED.timestamp
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
        cursor = self.execute(
            "SELECT * FROM interview_transcripts WHERE interview_id = %s", (interview_id,)
        )
        row = cursor.fetchone()
        return self._row_to_interview_transcript(row) if row else None

    @staticmethod
    def _row_to_interview_transcript(row: dict) -> InterviewTranscript:
        return InterviewTranscript(
            interview_id=row["interview_id"],
            employee_id=row["employee_id"],
            incident_id=row["incident_id"],
            transcript=row["transcript"],
            timestamp=row["timestamp"],
        )
