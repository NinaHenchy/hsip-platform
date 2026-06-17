"""HSIP Platform — Database Connection Manager"""

import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, event, text
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import SQLITE_DB_PATH


def get_engine():
    engine = create_engine(
        f"sqlite:///{SQLITE_DB_PATH}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def set_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return engine


def initialize_database():
    schema_path = Path(__file__).parent / "schemas" / "hsip_schema.sql"
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    try:
        sql = schema_path.read_text()
        stmts = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in stmts:
            try:
                conn.execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Schema: {e}")
        conn.commit()
        logger.success("HSIP database schema initialised.")
    finally:
        conn.close()
    return get_engine()


def test_connection():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.success("HSIP database connection OK.")
    return True
