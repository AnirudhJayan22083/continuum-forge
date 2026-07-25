"""Test connection to Neon PostgreSQL database and schema initialization."""

import sys
import logging
from pathlib import Path

# Add continuum package to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database, PostgresDatabase
from models.employee import Employee
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_neon_connection():
    logger.info("Initializing Neon PostgreSQL Database...")
    db = Database()
    logger.info(f"Database instance created: {type(db).__name__}")
    
    assert isinstance(db, PostgresDatabase), "Expected PostgresDatabase instance"
    
    db.connect()
    logger.info("Connecting to Neon DB...")
    db.init_schema()
    logger.info("Schema initialized successfully on Neon PostgreSQL!")
    
    # Test inserting an employee
    test_emp = Employee(
        employee_id="EMP_TEST_01",
        name="Neon Test Technician",
        machine_id="Machine-A",
        years_experience=15,
        retirement_date=date(2028, 12, 31),
        expertise_areas=["Hydraulics", "Bearings"],
        interview_completed=False
    )
    db.insert_employee(test_emp)
    logger.info("Inserted test employee into Neon DB.")
    
    fetched = db.get_employee("EMP_TEST_01")
    logger.info(f"Fetched employee from Neon DB: {fetched.name} ({fetched.employee_id})")
    assert fetched.employee_id == "EMP_TEST_01"
    
    db.close()
    logger.info("Neon PostgreSQL Database test completed successfully!")

if __name__ == "__main__":
    test_neon_connection()
