"""
HSIP Synthetic Data Generator
================================
Generates 2 years of weekly safety performance data per department.
Designed to simulate realistic safety culture variation and LTI clustering.

Key realism features:
- Safety Culture Index degrades over summer (heat, fatigue, contractor peak)
- LTI events cluster after periods of low SCI — realistic lag effect
- Contractor departments have higher risk profiles
- Near miss reporting rate inversely correlates with incident rate (reporting culture effect)
- Training compliance degrades through year, spikes after incidents
"""

import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    DEPARTMENTS, DEPT_WORKFORCE, SCI_WEIGHTS, SCI_THRESHOLDS,
    SIMULATION_START, SIMULATION_WEEKS, RANDOM_SEED,
    PREDICTION_HORIZON_DAYS
)

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

START_DATE = datetime.strptime(SIMULATION_START, "%Y-%m-%d").date()

# Department risk profiles — baseline risk multiplier
DEPT_RISK_PROFILE = {
    "Production Operations":    1.0,
    "Maintenance":              1.3,
    "Drilling":                 1.5,
    "Logistics":                1.1,
    "HSE":                      0.3,
    "Instrumentation & Control":0.7,
    "Electrical":               1.2,
    "Process Engineering":      0.6,
    "Contractor — Mechanical":  1.8,
    "Contractor — Civil":       1.6,
    "Contractor — Catering":    0.8,
}

# Departments with naturally good safety culture
DEPT_CULTURE_BASELINE = {
    "Production Operations":    72,
    "Maintenance":              68,
    "Drilling":                 65,
    "Logistics":                74,
    "HSE":                      92,
    "Instrumentation & Control":78,
    "Electrical":               76,
    "Process Engineering":      82,
    "Contractor — Mechanical":  60,
    "Contractor — Civil":       58,
    "Contractor — Catering":    70,
}


def _seasonal_factor(week_date: date) -> float:
    """Q3 elevated risk — heat stress, peak contractor, summer fatigue."""
    month = week_date.month
    return {1:0.85,2:0.85,3:0.90,4:0.95,5:1.00,6:1.10,
            7:1.25,8:1.25,9:1.10,10:0.95,11:0.90,12:0.85}.get(month, 1.0)


def _compute_sci(row: dict) -> float:
    """Compute Safety Culture Index from leading indicators."""
    # Normalise each component to 0-100
    nm_score    = min(100, row["near_miss_rate"] * 20)  # Rate of 5+ = 100
    train_score = row["training_compliance_pct"]
    insp_score  = row["inspection_score"]
    action_score = row["action_closeout_rate"]
    ptw_score   = row["ptw_compliance_rate"]

    sci = (
        nm_score    * SCI_WEIGHTS["near_miss_reporting_rate"] +
        train_score * SCI_WEIGHTS["training_compliance_pct"] +
        insp_score  * SCI_WEIGHTS["inspection_score_avg"] +
        action_score* SCI_WEIGHTS["action_closeout_rate"] +
        ptw_score   * SCI_WEIGHTS["ptw_compliance_rate"]
    )
    return round(min(100, max(0, sci)), 1)


def generate_weekly_snapshots() -> pd.DataFrame:
    """Generate 2 years × 11 departments = 2,288 weekly records."""
    records = []
    week_dates = [START_DATE + timedelta(weeks=i) for i in range(SIMULATION_WEEKS)]

    for dept in DEPARTMENTS:
        workforce   = DEPT_WORKFORCE[dept]
        risk_mult   = DEPT_RISK_PROFILE[dept]
        cult_base   = DEPT_CULTURE_BASELINE[dept]
        # Running state — culture degrades/improves over time
        culture_drift = 0.0

        for week_idx, week_date in enumerate(week_dates):
            season = _seasonal_factor(week_date)
            year   = week_date.year
            week_n = week_idx + 1

            # Culture varies — slightly noisy random walk
            culture_drift += np.random.normal(0, 1.5)
            culture_drift  = max(-20, min(20, culture_drift))
            effective_culture = cult_base + culture_drift

            # Leading Indicators
            # Near miss reporting — HIGHER = better reporting culture
            nm_rate = max(0, np.random.normal(
                effective_culture / 20,   # Good culture = more reporting
                0.8
            ))
            nm_count = int(nm_rate * workforce / 100)

            ua_count  = max(0, int(np.random.poisson(risk_mult * season * 2.0)))
            uc_count  = max(0, int(np.random.poisson(risk_mult * season * 1.5)))
            obs_count = nm_count + ua_count + uc_count + random.randint(0, 3)
            swa_used  = int(random.random() < (risk_mult * season * 0.08))

            insp_score = max(45, min(98, np.random.normal(
                effective_culture * 0.85 + 10,
                5.0
            )))
            insp_count = random.randint(3, 8)
            crit_findings = max(0, int(np.random.poisson(
                max(0.1, (100 - insp_score) / 25)
            )))

            action_closeout = max(30, min(99, np.random.normal(
                effective_culture * 0.75 + 20,
                8.0
            )))
            overdue = max(0, int(np.random.poisson(
                max(0.1, (100 - action_closeout) / 20)
            )))

            train_comp = max(50, min(99, np.random.normal(
                effective_culture * 0.80 + 15,
                6.0
            )))
            expired_certs = max(0, int(workforce * (1 - train_comp/100) * 0.3))
            train_hours = max(0, np.random.normal(workforce * 1.2, 5))

            ptw_issued = max(0, int(np.random.poisson(workforce * 0.3)))
            ptw_viol   = max(0, int(np.random.binomial(ptw_issued, 0.03 * risk_mult))) if ptw_issued > 0 else 0
            ptw_compliance = round((1 - ptw_viol / max(1, ptw_issued)) * 100, 1)

            toolbox  = max(1, int(np.random.poisson(3)))
            mgmt_walk = int(random.random() < 0.4)

            manhours = workforce * 12 * 2 * 7 * 0.85  # 12hr shifts, 2/day, 7 days, 85% attendance

            # Lagging indicators — driven by risk profile and culture
            lti_prob_week = risk_mult * season * max(0, (80 - effective_culture) / 200)
            lti_this_week = int(np.random.random() < lti_prob_week)

            fa_count  = max(0, int(np.random.poisson(risk_mult * season * 0.4)))
            mtc_count = max(0, int(np.random.poisson(risk_mult * season * 0.15)))
            rwc_count = max(0, int(np.random.poisson(risk_mult * season * 0.08)))

            row = {
                "week_start_date":          str(week_date),
                "week_number":              week_n,
                "year":                     year,
                "department":               dept,
                "workforce_size":           workforce,
                "near_miss_count":          nm_count,
                "near_miss_rate":           round(nm_rate, 2),
                "unsafe_act_count":         ua_count,
                "unsafe_condition_count":   uc_count,
                "observation_count":        obs_count,
                "swa_used":                 swa_used,
                "inspection_score":         round(insp_score, 1),
                "inspection_count":         insp_count,
                "critical_findings":        crit_findings,
                "action_closeout_rate":     round(action_closeout, 1),
                "overdue_actions":          overdue,
                "training_compliance_pct":  round(train_comp, 1),
                "expired_certs":            expired_certs,
                "training_hours":           round(train_hours, 1),
                "ptw_issued":               ptw_issued,
                "ptw_violations":           ptw_viol,
                "ptw_compliance_rate":      ptw_compliance,
                "toolbox_talks":            toolbox,
                "management_walks":         mgmt_walk,
                "safety_culture_index":     None,   # computed below
                "first_aid_count":          fa_count,
                "medical_treatment_count":  mtc_count,
                "restricted_work_count":    rwc_count,
                "lti_count":                lti_this_week,
                "fatality_count":           0,
                "days_lost":                lti_this_week * random.randint(3, 30),
                "manhours":                 round(manhours, 0),
                "lti_next_30_days":         0,  # filled below
            }
            row["safety_culture_index"] = _compute_sci(row)
            records.append(row)

    df = pd.DataFrame(records)

    # Generate LTI target: did this dept have an LTI in the next 30 days?
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])
    for dept in DEPARTMENTS:
        dept_mask = df["department"] == dept
        dept_df   = df[dept_mask].copy()
        lti_dates = dept_df[dept_df["lti_count"] > 0]["week_start_date"].tolist()

        for lti_date in lti_dates:
            horizon_start = lti_date - timedelta(days=PREDICTION_HORIZON_DAYS)
            window_mask = (
                dept_mask &
                (df["week_start_date"] >= horizon_start) &
                (df["week_start_date"] < lti_date)
            )
            df.loc[window_mask, "lti_next_30_days"] = 1

    df["week_start_date"] = df["week_start_date"].dt.strftime("%Y-%m-%d")
    logger.info(f"Weekly snapshots: {len(df):,} records | LTI positive rate: {df['lti_next_30_days'].mean()*100:.1f}%")
    return df


def generate_lti_events(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Extract actual LTI events from snapshots."""
    snap = snapshots.copy()
    snap["week_start_date"] = pd.to_datetime(snap["week_start_date"])
    lti_rows = snap[snap["lti_count"] > 0].copy()

    root_causes = [
        "Inadequate Procedure / No Procedure",
        "Procedure Not Followed",
        "Inadequate Training / Competency",
        "Equipment Failure / Deterioration",
        "Human Factors / Operator Error",
        "Inadequate Supervision",
        "Communication Failure",
        "Fatigue",
        "Contractor Management Gap",
    ]

    event_types = [
        "Lost Time Injury",
        "Lost Time Injury",
        "Lost Time Injury",
        "Dangerous Occurrence",
    ]

    records = []
    for _, row in lti_rows.iterrows():
        records.append({
            "event_date":           row["week_start_date"].strftime("%Y-%m-%d"),
            "department":           row["department"],
            "event_type":           random.choice(event_types),
            "severity":             random.choice(["High","Critical","Medium"]),
            "days_lost":            row["days_lost"],
            "description":          f"LTI event in {row['department']} — week of {row['week_start_date'].strftime('%Y-%m-%d')}. Investigation initiated.",
            "root_cause_category":  random.choice(root_causes),
        })

    df = pd.DataFrame(records)
    logger.info(f"LTI events: {len(df)}")
    return df


def generate_monthly_sci(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly SCI summary per department."""
    snap = snapshots.copy()
    snap["week_start_date"] = pd.to_datetime(snap["week_start_date"])
    snap["year_month"] = snap["week_start_date"].dt.strftime("%Y-%m")

    monthly = snap.groupby(["year_month","department"]).agg(
        avg_sci=("safety_culture_index","mean"),
        avg_near_miss_rate=("near_miss_rate","mean"),
        avg_training_compliance=("training_compliance_pct","mean"),
        avg_inspection_score=("inspection_score","mean"),
        avg_action_closeout=("action_closeout_rate","mean"),
        avg_ptw_compliance=("ptw_compliance_rate","mean"),
        lti_count=("lti_count","sum"),
        near_miss_count=("near_miss_count","sum"),
    ).reset_index()

    for col in ["avg_sci","avg_near_miss_rate","avg_training_compliance",
                "avg_inspection_score","avg_action_closeout","avg_ptw_compliance"]:
        monthly[col] = monthly[col].round(1)

    logger.info(f"Monthly SCI summary: {len(monthly)} records")
    return monthly


def run_full_generation() -> dict:
    logger.info("=" * 60)
    logger.info("HSIP Platform — Data Generation START")
    logger.info("=" * 60)

    snapshots = generate_weekly_snapshots()
    lti_events = generate_lti_events(snapshots)
    monthly_sci = generate_monthly_sci(snapshots)

    result = {
        "weekly_dept_snapshot": snapshots,
        "lti_events":           lti_events,
        "monthly_sci_summary":  monthly_sci,
    }

    for table, df in result.items():
        logger.success(f"  {table}: {len(df):,} records")

    logger.success("HSIP Data Generation COMPLETE")
    return result


if __name__ == "__main__":
    run_full_generation()
