"""HSIP Platform — Database Loader"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd
from loguru import logger
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from database.db_connection import get_engine
from config.settings import SQLITE_DB_PATH

CORE_TABLES = [
    "weekly_dept_snapshot",
    "lti_events",
    "monthly_sci_summary",
]


def _truncate_core():
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        for t in reversed(CORE_TABLES):
            try:
                conn.execute(f"DELETE FROM {t}")
            except Exception:
                pass  # Table may not exist yet on first run
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    finally:
        conn.close()


def load_all_tables(datasets: dict, engine=None) -> dict:
    if engine is None:
        engine = get_engine()
    _truncate_core()
    summary = {}
    for table, df in datasets.items():
        if df is None or df.empty:
            continue
        rows = len(df)
        df.to_sql(table, con=engine, if_exists="append",
                  index=False, chunksize=500, method="multi")
        logger.success(f"  {table}: {rows:,} rows")
        summary[table] = rows
    return summary


def verify_load(engine=None) -> pd.DataFrame:
    if engine is None:
        engine = get_engine()
    rows = []
    with engine.connect() as conn:
        for t in CORE_TABLES:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            rows.append({"table": t, "rows": count})
            logger.success(f"  {t}: {count:,}")
    return pd.DataFrame(rows)
