"""Synthetic data generator for CONTINUUM."""

import json
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import random
import numpy as np

logger = logging.getLogger(__name__)

# Machines and technicians
MACHINES = ["MACHINE-A", "MACHINE-B", "MACHINE-C"]
BASE_DATE = datetime(2026, 1, 1)
DATE_RANGE_DAYS = 206  # 2026-01-01 to 2026-07-25

# Probability that a sensor reading LINKED to a bearing-failure incident
# actually exhibits the humidity/vibration pattern (allows some realistic
# noise rather than a perfectly deterministic signal).
BEARING_PATTERN_HIT_RATE = 0.90
# Probability that a sensor reading linked to a NON-bearing incident
# happens to exhibit the pattern anyway (background noise / false positives).
OTHER_PATTERN_HIT_RATE = 0.08
# Probability a general background reading (not tied to any incident)
# exhibits the pattern.
BACKGROUND_PATTERN_RATE = 0.30


class SyntheticDataGenerator:
    """Generate synthetic datasets for CONTINUUM.

    Maintenance logs and sensor readings are NOT generated independently.
    Every maintenance log is paired with a sensor reading captured shortly
    before it, on the same machine. Bearing-failure logs are paired with
    readings that (mostly) satisfy the humidity>80% AND vibration>2.0mm/s
    pattern; other logs are paired with readings that (mostly) don't.
    This is what makes the embedded pattern statistically detectable by
    the ValidationEngine later, rather than existing only in prose
    descriptions.
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize generator.

        Args:
            data_dir: Directory to store generated data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        random.seed(42)
        np.random.seed(42)

    def generate_employees(self) -> List[dict]:
        """Generate synthetic employee data."""
        employees = [
            {
                "employee_id": "EMP001",
                "name": "John Smith",
                "machine_id": "MACHINE-A",
                "years_experience": 25,
                "retirement_date": "2026-12-31",
                "expertise_areas": "bearing maintenance,vibration analysis",
                "interview_completed": False,
            },
            {
                "employee_id": "EMP002",
                "name": "Maria Garcia",
                "machine_id": "MACHINE-B",
                "years_experience": 18,
                "retirement_date": "2027-06-30",
                "expertise_areas": "hydraulic systems,pressure regulation",
                "interview_completed": False,
            },
            {
                "employee_id": "EMP003",
                "name": "Robert Chen",
                "machine_id": "MACHINE-C",
                "years_experience": 12,
                "retirement_date": "2028-03-15",
                "expertise_areas": "electrical systems,sensor calibration",
                "interview_completed": False,
            },
        ]
        return employees

    def generate_maintenance_logs(self) -> List[dict]:
        """Generate synthetic maintenance logs.

        92 total: 30 bearing failures (positive occurrences for the
        embedded pattern) and 62 other events (negative occurrences).

        Returns:
            List of maintenance log dictionaries, each including a
            "_timestamp_dt" datetime object for internal use when
            generating the linked sensor reading.
        """
        logs = []
        base_date = BASE_DATE

        for i in range(92):
            log_id = i + 1
            days_offset = random.randint(0, DATE_RANGE_DAYS)
            timestamp = base_date + timedelta(days=days_offset)

            if i < 30:
                # Positive occurrence: bearing failure
                machine_id = random.choice(["MACHINE-A", "MACHINE-B"])
                component = "bearing"
                failure_type = "bearing_failure"
                description = "Bearing overheated due to high humidity and vibration"
                resolution = "Replaced bearing, cleaned lubrication system"
                technician_id = random.choice(["EMP001", "EMP002"])
            else:
                # Negative occurrence: unrelated failure/maintenance
                machine_id = random.choice(MACHINES)
                failure_types = [
                    "seal_wear",
                    "oil_degradation",
                    "routine_maintenance",
                    "filter_replacement",
                    "alignment_check",
                ]
                failure_type = random.choice(failure_types)
                component = random.choice(["seal", "filter", "oil", "alignment"])
                description = f"Routine {component} maintenance"
                resolution = f"Replaced {component}"
                technician_id = random.choice(["EMP001", "EMP002", "EMP003"])

            logs.append(
                {
                    "log_id": f"LOG{log_id:04d}",
                    "machine_id": machine_id,
                    "component": component,
                    "failure_type": failure_type,
                    "timestamp": timestamp.isoformat(),
                    "_timestamp_dt": timestamp,
                    "description": description,
                    "technician_id": technician_id,
                    "resolution": resolution,
                }
            )

        return logs

    def _generate_linked_reading(self, log: dict, reading_id: int) -> dict:
        """Generate a sensor reading tied to a specific maintenance log.

        The reading is timestamped 1-8 hours before the incident, on the
        same machine, and its humidity/vibration values are drawn based
        on whether this log is a bearing failure (should usually show
        the pattern) or not (should usually not).
        """
        is_bearing = log["failure_type"] == "bearing_failure"
        hit_rate = BEARING_PATTERN_HIT_RATE if is_bearing else OTHER_PATTERN_HIT_RATE
        exhibits_pattern = random.random() < hit_rate

        hours_before = random.uniform(1, 8)
        timestamp = log["_timestamp_dt"] - timedelta(hours=hours_before)

        if exhibits_pattern:
            humidity = random.uniform(80, 95)
            vibration = random.uniform(2.0, 3.5)
        else:
            humidity = random.uniform(30, 75)
            vibration = random.uniform(0.5, 1.8)

        temperature = random.uniform(60, 85)
        pressure = random.uniform(5.0, 7.5)

        return {
            "reading_id": f"SENSOR{reading_id:05d}",
            "machine_id": log["machine_id"],
            "timestamp": timestamp.isoformat(),
            "_timestamp_dt": timestamp,
            "humidity_percent": round(humidity, 2),
            "vibration_mm_s": round(vibration, 2),
            "temperature_celsius": round(temperature, 2),
            "pressure_bar": round(pressure, 2),
        }

    def _generate_background_reading(self, reading_id: int) -> dict:
        """Generate a background sensor reading not tied to any incident."""
        days_offset = random.randint(0, DATE_RANGE_DAYS)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        timestamp = BASE_DATE + timedelta(
            days=days_offset, hours=hours_offset, minutes=minutes_offset
        )
        machine_id = random.choice(MACHINES)

        if random.random() < BACKGROUND_PATTERN_RATE:
            humidity = random.uniform(80, 95)
            vibration = random.uniform(2.0, 3.5)
        else:
            humidity = random.uniform(30, 75)
            vibration = random.uniform(0.5, 1.8)

        temperature = random.uniform(60, 85)
        pressure = random.uniform(5.0, 7.5)

        return {
            "reading_id": f"SENSOR{reading_id:05d}",
            "machine_id": machine_id,
            "timestamp": timestamp.isoformat(),
            "_timestamp_dt": timestamp,
            "humidity_percent": round(humidity, 2),
            "vibration_mm_s": round(vibration, 2),
            "temperature_celsius": round(temperature, 2),
            "pressure_bar": round(pressure, 2),
        }

    def generate_sensor_history(self, logs: List[dict], total_readings: int = 500) -> List[dict]:
        """Generate synthetic sensor history, linked to maintenance logs.

        One reading is generated per maintenance log (so the embedded
        pattern is actually statistically present), and the remainder
        are background readings to reach `total_readings`.

        Args:
            logs: Maintenance logs from generate_maintenance_logs().
            total_readings: Total number of sensor readings to produce.

        Returns:
            List of sensor reading dictionaries, sorted by timestamp.
        """
        readings = []
        reading_id = 0

        for log in logs:
            reading_id += 1
            readings.append(self._generate_linked_reading(log, reading_id))

        remaining = max(total_readings - len(logs), 0)
        for _ in range(remaining):
            reading_id += 1
            readings.append(self._generate_background_reading(reading_id))

        readings.sort(key=lambda r: r["_timestamp_dt"])
        return readings

    def generate_interview_transcripts(self) -> dict:
        """Generate synthetic interview transcripts."""
        transcripts = {
            "INT001": {
                "employee_id": "EMP001",
                "incident_id": "LOG0001",
                "timestamp": "2026-07-20T15:00:00",
                "transcript": """
Q: Tell me about the bearing failure incident on July 20th.
A: It was a hot, humid day. The humidity in the plant was around 85%. I noticed the bearing 
   was making noise and the vibration was increasing. We measured about 2.3 mm/s of vibration.
   The bearing was overheating. I immediately shut down the machine and replaced the bearing.

Q: Have you seen this pattern before?
A: Yes, many times. When humidity gets above 80% and vibration starts increasing, it's almost 
   always a bearing issue. The moisture affects the lubrication, and the vibration accelerates 
   the wear. I'd say I'm 95% confident in this pattern.

Q: What's your recommended action?
A: Monitor humidity and vibration closely. If both are elevated, replace the bearing before 
   it fails completely. Clean the lubrication system and use moisture-resistant grease.
""",
            },
            "INT002": {
                "employee_id": "EMP002",
                "incident_id": "LOG0015",
                "timestamp": "2026-07-21T10:30:00",
                "transcript": """
Q: Tell me about the hydraulic system issue you handled.
A: The pressure was fluctuating. We had a seal that was wearing out. The system was losing 
   pressure gradually over a few days.

Q: What patterns have you noticed with hydraulic failures?
A: Pressure drops are usually seal wear. Temperature also matters - if it gets too hot, 
   the seals degrade faster. I've seen this happen on Tuesdays more often, but I think 
   that's just because we run heavier loads on Mondays.

Q: How confident are you in that Tuesday pattern?
A: Not very confident, maybe 40%. It could just be coincidence. The real indicator is 
   the pressure drop rate and temperature.
""",
            },
            "INT003": {
                "employee_id": "EMP003",
                "incident_id": "LOG0030",
                "timestamp": "2026-07-22T14:00:00",
                "transcript": """
Q: Tell me about the sensor calibration issue.
A: The vibration sensor was reading incorrectly. It was drifting over time. We recalibrated 
   it against the reference standard.

Q: How often do you see sensor drift?
A: About once every 3-4 months. It's usually due to temperature changes or mechanical shock. 
   The sensors need regular maintenance and recalibration.

Q: Any patterns you've noticed?
A: Not really. It's pretty random. Sometimes it happens after a heavy maintenance day, 
   but not always. I'd say sensor drift is unpredictable.
""",
            },
        }
        return transcripts

    @staticmethod
    def _strip_internal_fields(rows: List[dict]) -> List[dict]:
        """Remove internal-only keys (prefixed with '_') before saving to disk."""
        return [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]

    def save_employees_csv(self, employees: List[dict]) -> None:
        """Save employees to CSV."""
        csv_path = self.data_dir / "employees.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=employees[0].keys())
            writer.writeheader()
            writer.writerows(employees)
        logger.info(f"Saved employees to {csv_path}")

    def save_maintenance_logs_csv(self, logs: List[dict]) -> None:
        """Save maintenance logs to CSV."""
        clean_logs = self._strip_internal_fields(logs)
        csv_path = self.data_dir / "maintenance_logs.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=clean_logs[0].keys())
            writer.writeheader()
            writer.writerows(clean_logs)
        logger.info(f"Saved maintenance logs to {csv_path}")

    def save_sensor_history_csv(self, readings: List[dict]) -> None:
        """Save sensor history to CSV."""
        clean_readings = self._strip_internal_fields(readings)
        csv_path = self.data_dir / "sensor_history.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=clean_readings[0].keys())
            writer.writeheader()
            writer.writerows(clean_readings)
        logger.info(f"Saved sensor history to {csv_path}")

    def save_interview_transcripts_json(self, transcripts: dict) -> None:
        """Save interview transcripts to JSON."""
        json_path = self.data_dir / "interview_transcripts.json"
        with open(json_path, "w") as f:
            json.dump(transcripts, f, indent=2)
        logger.info(f"Saved interview transcripts to {json_path}")

    def generate_all(self) -> None:
        """Generate all synthetic datasets.

        Order matters: maintenance logs are generated first, then sensor
        history is generated FROM the logs so each incident has a linked,
        pattern-consistent reading.
        """
        logger.info("Generating synthetic datasets...")

        employees = self.generate_employees()
        logs = self.generate_maintenance_logs()
        readings = self.generate_sensor_history(logs)
        transcripts = self.generate_interview_transcripts()

        self.save_employees_csv(employees)
        self.save_maintenance_logs_csv(logs)
        self.save_sensor_history_csv(readings)
        self.save_interview_transcripts_json(transcripts)

        logger.info("Synthetic datasets generated successfully")