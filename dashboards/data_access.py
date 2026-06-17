"""HSIP Platform — Data Access Layer"""

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.db_connection import get_engine
from config.settings import DEPARTMENTS, SCI_THRESHOLDS

_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def sql(query: str, params: dict = None) -> pd.DataFrame:
    try:
        return pd.read_sql(query, engine(), params=params)
    except Exception:
        return pd.DataFrame()


def get_weekly_snapshots(dept: str = None) -> pd.DataFrame:
    q = "SELECT * FROM weekly_dept_snapshot"
    if dept:
        q += f" WHERE department = '{dept}'"
    q += " ORDER BY week_start_date, department"
    return sql(q)


def get_latest_week_all_depts() -> pd.DataFrame:
    return sql("""
        SELECT * FROM weekly_dept_snapshot
        WHERE week_start_date = (
            SELECT MAX(week_start_date) FROM weekly_dept_snapshot
        )
        ORDER BY safety_culture_index ASC
    """)


def get_monthly_sci() -> pd.DataFrame:
    return sql("SELECT * FROM monthly_sci_summary ORDER BY year_month, department")


def get_lti_events() -> pd.DataFrame:
    return sql("SELECT * FROM lti_events ORDER BY event_date DESC")


def get_predictions() -> pd.DataFrame:
    return sql("""
        SELECT * FROM model_predictions
        ORDER BY prediction_date DESC, lti_probability_30d DESC
    """)


def get_dept_trend(dept: str) -> pd.DataFrame:
    return sql(f"""
        SELECT week_start_date, safety_culture_index,
               near_miss_rate, training_compliance_pct,
               inspection_score, action_closeout_rate,
               lti_count, lti_next_30_days
        FROM weekly_dept_snapshot
        WHERE department = '{dept}'
        ORDER BY week_start_date
    """)


def get_facility_sci_summary() -> dict:
    latest = get_latest_week_all_depts()
    monthly = get_monthly_sci()
    lti = get_lti_events()

    if latest.empty:
        return {}

    avg_sci = latest["safety_culture_index"].mean()
    worst_dept = latest.iloc[0]["department"]
    worst_sci = latest.iloc[0]["safety_culture_index"]
    best_dept = latest.iloc[-1]["department"]
    best_sci = latest.iloc[-1]["safety_culture_index"]
    total_ltis = len(lti)
    total_nm = latest["near_miss_count"].sum()
    avg_training = latest["training_compliance_pct"].mean()
    avg_inspection = latest["inspection_score"].mean()

    if avg_sci >= SCI_THRESHOLDS["excellent"]:   sci_rag = "excellent"
    elif avg_sci >= SCI_THRESHOLDS["good"]:       sci_rag = "good"
    elif avg_sci >= SCI_THRESHOLDS["fair"]:       sci_rag = "fair"
    else:                                          sci_rag = "poor"

    return {
        "avg_sci":              round(avg_sci, 1),
        "worst_dept":           worst_dept,
        "worst_sci":            round(worst_sci, 1),
        "best_dept":            best_dept,
        "best_sci":             round(best_sci, 1),
        "total_ltis_ytd":       total_ltis,
        "total_near_misses":    int(total_nm),
        "avg_training_compliance": round(avg_training, 1),
        "avg_inspection_score": round(avg_inspection, 1),
        "sci_rag":              sci_rag,
        "dept_count":           len(latest),
        "high_risk_depts":      int((latest["safety_culture_index"] < 65).sum()),
    }
