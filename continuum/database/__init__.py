"""Database module for CONTINUUM."""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

from .sqlite import Database as SQLiteDatabase
from .postgres import PostgresDatabase

logger = logging.getLogger(__name__)


def Database(db_path: str = "data/continuum.db", db_url: str = None):
    """Database factory function that returns either a Neon PostgreSQL or SQLite database instance.

    If `db_url` is provided or if DATABASE_URL / NEON_DATABASE_URL environment variable is set,
    it returns a PostgresDatabase connected to Neon. Otherwise, it defaults to SQLite.
    """
    url = db_url or os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
    if url:
        logger.info("Using Neon PostgreSQL Database connection")
        return PostgresDatabase(db_url=url)
    else:
        logger.info("Using SQLite Database connection")
        return SQLiteDatabase(db_path=db_path)


__all__ = ["Database", "SQLiteDatabase", "PostgresDatabase"]
