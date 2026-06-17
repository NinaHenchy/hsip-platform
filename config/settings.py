"""
HSIP Platform Configuration
============================
HSE Incident Prediction & Safety Culture Intelligence Platform
Facility: Offshore Production Complex OPC-Alpha

Unique positioning:
- Predicts LTI probability 30 days ahead from leading indicators
- Quantifies Safety Culture Index (SCI) per department
- Identifies which leading indicators are strongest predictors of harm
- First platform in the portfolio that is PURELY PREDICTIVE on safety data
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# BASE PATHS
# ─────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
SQLITE_DB_PATH = BASE_DIR / "database" / "hsip_dev.db"
LOGS_DIR    = BASE_DIR / "logs"
MODELS_DIR  = BASE_DIR / "models"
DATA_DIR    = BASE_DIR / "data"

# ─────────────────────────────────────────────
# FACILITY
# ─────────────────────────────────────────────
FACILITY_NAME   = "Offshore Production Complex — OPC-Alpha"
FACILITY_CODE   = "OPC-A"
WORKFORCE_SIZE  = 285
SIMULATION_START = "2023-01-01"
SIMULATION_WEEKS = 104   # 2 years of weekly data

# ─────────────────────────────────────────────
# DEPARTMENTS (11 operational departments)
# ─────────────────────────────────────────────
DEPARTMENTS = [
    "Production Operations",
    "Maintenance",
    "Drilling",
    "Logistics",
    "HSE",
    "Instrumentation & Control",
    "Electrical",
    "Process Engineering",
    "Contractor — Mechanical",
    "Contractor — Civil",
    "Contractor — Catering",
]

DEPT_WORKFORCE = {
    "Production Operations":    45,
    "Maintenance":              38,
    "Drilling":                 35,
    "Logistics":                22,
    "HSE":                      12,
    "Instrumentation & Control":18,
    "Electrical":               15,
    "Process Engineering":      14,
    "Contractor — Mechanical":  35,
    "Contractor — Civil":       28,
    "Contractor — Catering":    23,
}

# ─────────────────────────────────────────────
# SAFETY CULTURE INDEX (SCI) WEIGHTS
# SCI = weighted composite of leading indicators
# ─────────────────────────────────────────────
SCI_WEIGHTS = {
    "near_miss_reporting_rate": 0.25,   # Near misses per 100 workers per week
    "training_compliance_pct":  0.25,   # % workforce with valid mandatory certs
    "inspection_score_avg":     0.20,   # Weekly inspection score (0-100)
    "action_closeout_rate":     0.20,   # % corrective actions closed on time
    "ptw_compliance_rate":      0.10,   # % PTW issued with no violations
}

# ─────────────────────────────────────────────
# PREDICTION TARGET
# ─────────────────────────────────────────────
# Binary: Will this department have an LTI in the next 30 days?
PREDICTION_HORIZON_DAYS = 30
LTI_TYPES = [
    "Lost Time Injury",
    "Fatality",
    "Dangerous Occurrence",
]

# ─────────────────────────────────────────────
# THEME — Teal/Green (distinct from ORPMI blue and HSEI red)
# ─────────────────────────────────────────────
THEME_PRIMARY   = "#0d7377"   # Deep teal
THEME_SECONDARY = "#14a085"   # Emerald
THEME_ACCENT    = "#f0a500"   # Amber gold
THEME_DANGER    = "#c0392b"   # Red
THEME_BG        = "#f0f7f7"   # Teal tint background
THEME_CARD      = "#ffffff"
THEME_BORDER    = "#c8dede"
THEME_TEXT      = "#0d2b2b"
THEME_MUTED     = "#4a7070"

# ─────────────────────────────────────────────
# SCI BENCHMARKS
# ─────────────────────────────────────────────
SCI_THRESHOLDS = {
    "excellent":    85,
    "good":         70,
    "fair":         55,
    "poor":         40,
}

# ─────────────────────────────────────────────
# ML PARAMETERS
# ─────────────────────────────────────────────
RANDOM_SEED     = 42
TEST_WEEKS      = 20   # Last 20 weeks = test set
TRAIN_WEEKS     = 84   # First 84 weeks = training set


# ─────────────────────────────────────────────
# DEPARTMENT RISK PROFILES
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# DB TYPE
# ─────────────────────────────────────────────
DB_TYPE = "sqlite"
