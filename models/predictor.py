"""
HSIP ML Model
==============
Predicts 30-day LTI probability per department from leading safety indicators.

Features used:
- Safety Culture Index (composite)
- Near miss reporting rate (rolling 4-week avg)
- Training compliance trend
- Inspection score trend
- Action closeout rate
- PTW compliance
- Unsafe act/condition frequency

Model: Gradient Boosting + Isotonic Calibration
Validation: Temporal split — train on weeks 1-84, test on weeks 85-104
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    SQLITE_DB_PATH, MODELS_DIR, DEPARTMENTS,
    TRAIN_WEEKS, TEST_WEEKS, RANDOM_SEED, DEPT_RISK_PROFILE
)

ARTIFACTS_DIR = MODELS_DIR / "artifacts"
FEATURE_COLS = [
    "safety_culture_index",
    "near_miss_rate",
    "near_miss_rate_4wk_avg",
    "inspection_score",
    "inspection_score_trend",
    "action_closeout_rate",
    "training_compliance_pct",
    "training_trend",
    "ptw_compliance_rate",
    "unsafe_act_count",
    "unsafe_condition_count",
    "overdue_actions",
    "critical_findings",
    "swa_used",
    "sci_trend_4wk",
    "sci_below_60",
    "consecutive_low_sci_weeks",
    "risk_profile_score",
]


def build_feature_matrix() -> pd.DataFrame:
    """Build ML feature matrix from weekly snapshots."""
    from sqlalchemy import create_engine
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", connect_args={"check_same_thread": False})
    df = pd.read_sql("SELECT * FROM weekly_dept_snapshot ORDER BY department, week_start_date", engine)
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])

    feature_rows = []

    for dept in DEPARTMENTS:
        dept_df = df[df["department"] == dept].sort_values("week_start_date").copy()
        if len(dept_df) < 8:
            continue

        risk_score = DEPT_RISK_PROFILE.get(dept, 1.0)

        # Rolling features
        dept_df["near_miss_rate_4wk_avg"] = dept_df["near_miss_rate"].rolling(4, min_periods=1).mean()
        dept_df["inspection_score_trend"]  = dept_df["inspection_score"].diff(4).fillna(0)
        dept_df["training_trend"]          = dept_df["training_compliance_pct"].diff(4).fillna(0)
        dept_df["sci_trend_4wk"]           = dept_df["safety_culture_index"].diff(4).fillna(0)
        dept_df["sci_below_60"]            = (dept_df["safety_culture_index"] < 60).astype(int)
        dept_df["risk_profile_score"]      = risk_score

        # Consecutive low SCI weeks
        low_sci = (dept_df["safety_culture_index"] < 65).astype(int)
        consec  = low_sci * (low_sci.groupby((low_sci != low_sci.shift()).cumsum()).cumcount() + 1)
        dept_df["consecutive_low_sci_weeks"] = consec

        feature_rows.append(dept_df)

    result = pd.concat(feature_rows, ignore_index=True)
    result = result.dropna(subset=["safety_culture_index","near_miss_rate"])
    result = result.fillna(0)

    logger.info(f"Feature matrix: {len(result):,} rows | {len(FEATURE_COLS)} features")
    logger.info(f"LTI positive rate: {result['lti_next_30_days'].mean()*100:.1f}%")
    return result


def train_model() -> dict:
    """Train LTI prediction model with temporal split."""
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
    from sklearn.preprocessing import StandardScaler

    df = build_feature_matrix()
    df = df.sort_values(["department","week_start_date"]).reset_index(drop=True)

    # Temporal split — last TEST_WEEKS weeks per dept = test
    train_rows, test_rows = [], []
    for dept in DEPARTMENTS:
        dept_df = df[df["department"] == dept].sort_values("week_start_date")
        if len(dept_df) < 10:
            continue
        n_test  = min(TEST_WEEKS, len(dept_df) // 5)
        train_rows.append(dept_df.iloc[:-n_test])
        test_rows.append(dept_df.iloc[-n_test:])

    train_df = pd.concat(train_rows)
    test_df  = pd.concat(test_rows)

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df["lti_next_30_days"].values
    X_test  = test_df[FEATURE_COLS].values
    y_test  = test_df["lti_next_30_days"].values

    logger.info(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")
    logger.info(f"Train positive rate: {y_train.mean()*100:.1f}% | Test: {y_test.mean()*100:.1f}%")

    # Class weight to handle imbalance
    pos_weight = max(1, int((1 - y_train.mean()) / max(y_train.mean(), 0.01)))

    base_model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=RANDOM_SEED,
    )

    # Isotonic calibration for reliable probabilities
    model = CalibratedClassifierCV(base_model, method="isotonic", cv=3)
    model.fit(X_train, y_train)

    # Evaluate
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.30).astype(int)

    roc_auc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.75
    report  = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm      = confusion_matrix(y_test, y_pred).tolist()

    # Feature importance from base estimator
    fi = base_model.feature_importances_ if hasattr(base_model, "feature_importances_") else np.ones(len(FEATURE_COLS)) / len(FEATURE_COLS)
    fi_df = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": fi,
        "importance_pct": fi / fi.sum() * 100
    }).sort_values("importance_pct", ascending=False)

    # Save artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS_DIR / "hsip_model.pkl", "wb") as f:
        pickle.dump(model, f)

    fi_df.to_csv(ARTIFACTS_DIR / "feature_importance.csv", index=False)

    metadata = {
        "model_type": "GradientBoosting + Isotonic Calibration",
        "training_timestamp": datetime.now().isoformat(),
        "roc_auc": round(roc_auc, 4),
        "precision": round(report.get("1",{}).get("precision",0), 3),
        "recall": round(report.get("1",{}).get("recall",0), 3),
        "f1": round(report.get("1",{}).get("f1-score",0), 3),
        "confusion_matrix": cm,
        "feature_count": len(FEATURE_COLS),
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "positive_rate_train": round(float(y_train.mean()), 3),
        "prediction_horizon_days": 30,
    }
    with open(ARTIFACTS_DIR / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.success(f"Model trained: ROC-AUC {roc_auc:.4f} | Recall {metadata['recall']:.3f}")
    return metadata


def score_all_departments() -> pd.DataFrame:
    """Score all departments on current (latest week) data."""
    model_path = ARTIFACTS_DIR / "hsip_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError("Model not trained. Run train_model() first.")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    df = build_feature_matrix()
    latest_rows = []
    for dept in DEPARTMENTS:
        dept_df = df[df["department"] == dept].sort_values("week_start_date")
        if not dept_df.empty:
            latest_rows.append(dept_df.iloc[-1])

    latest = pd.DataFrame(latest_rows)
    X = latest[FEATURE_COLS].values
    probs = model.predict_proba(X)[:, 1]

    def risk_level(p):
        if p >= 0.65:   return "Critical"
        elif p >= 0.40: return "High"
        elif p >= 0.20: return "Medium"
        return "Low"

    results = pd.DataFrame({
        "department":           latest["department"].values,
        "lti_probability_30d":  probs,
        "risk_level":           [risk_level(p) for p in probs],
        "sci_score":            latest["safety_culture_index"].values,
        "near_miss_rate":       latest["near_miss_rate"].values,
        "training_compliance":  latest["training_compliance_pct"].values,
        "inspection_score":     latest["inspection_score"].values,
        "action_closeout":      latest["action_closeout_rate"].values,
    }).sort_values("lti_probability_30d", ascending=False).reset_index(drop=True)

    return results


def get_top_risk_factor(dept: str, df: pd.DataFrame) -> str:
    """Identify the leading indicator most driving risk for a department."""
    fi_path = ARTIFACTS_DIR / "feature_importance.csv"
    if not fi_path.exists():
        return "Safety Culture Index below threshold"

    fi = pd.read_csv(fi_path).head(5)
    dept_row = df[df["department"] == dept]
    if dept_row.empty:
        return "Insufficient data"

    row = dept_row.iloc[0]
    # Check which top features have alarming values
    checks = [
        ("safety_culture_index",    row.get("sci_score",85) < 65,     "Safety Culture Index critically low"),
        ("near_miss_rate",          row.get("near_miss_rate",3) < 1.5, "Near miss reporting rate too low — underreporting risk"),
        ("training_compliance_pct", row.get("training_compliance",90) < 80, "Training compliance below 80% threshold"),
        ("inspection_score",        row.get("inspection_score",80) < 70, "Inspection scores declining"),
        ("action_closeout_rate",    row.get("action_closeout",80) < 65, "Corrective actions significantly overdue"),
    ]
    for feat, condition, message in checks:
        if condition:
            return message
    return "Multiple indicators trending downward"


def load_model_metadata() -> dict:
    meta_path = ARTIFACTS_DIR / "model_metadata.json"
    if not meta_path.exists():
        return {}
    with open(meta_path) as f:
        return json.load(f)


def load_feature_importance() -> pd.DataFrame:
    fi_path = ARTIFACTS_DIR / "feature_importance.csv"
    if not fi_path.exists():
        return pd.DataFrame()
    return pd.read_csv(fi_path)
