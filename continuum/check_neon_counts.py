"""Check row counts of all tables in Neon PostgreSQL database."""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import Database, PostgresDatabase

def check_neon_counts():
    db = Database()
    print("Using DB Class:", type(db).__name__)
    db.connect()
    
    tables = [
        "employees",
        "maintenance_logs",
        "sensor_readings",
        "heuristics",
        "validation_results",
        "operational_rules",
        "interview_transcripts"
    ]
    
    print("\n--- Neon PostgreSQL Database Table Row Counts ---")
    for table in tables:
        cursor = db.execute(f"SELECT COUNT(*) as count FROM {table}")
        res = cursor.fetchone()
        count = res["count"] if res else 0
        print(f"Table '{table}': {count} rows")
    
    db.close()

if __name__ == "__main__":
    check_neon_counts()
