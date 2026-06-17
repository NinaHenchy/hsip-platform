"""
HSIP Platform — Test Suite
Run: pytest tests/test_hsip.py -v
"""

import sys
import pytest
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def engine():
    from database.db_connection import get_engine
    return get_engine()


@pytest.fixture(scope="session")
def snapshots(engine):
    return pd.read_sql("SELECT * FROM weekly_dept_snapshot", engine)


@pytest.fixture(scope="session")
def monthly(engine):
    return pd.read_sql("SELECT * FROM monthly_sci_summary", engine)


class TestDatabase:
    def test_connection(self, engine):
        from sqlalchemy import text
        with engine.connect() as conn:
            assert conn.execute(text("SELECT 1")).scalar() == 1

    def test_tables_populated(self, engine):
        from sqlalchemy import text
        with engine.connect() as conn:
            for t in ["weekly_dept_snapshot","lti_events","monthly_sci_summary"]:
                r = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                assert r > 0, f"{t} is empty"

    def test_snapshot_count(self, snapshots):
        # 11 departments × 104 weeks = 1144
        assert len(snapshots) >= 1000

    def test_monthly_count(self, monthly):
        assert len(monthly) >= 100  # 11 depts × ~24 months


class TestSnapshots:
    def test_sci_range(self, snapshots):
        assert (snapshots["safety_culture_index"] >= 0).all()
        assert (snapshots["safety_culture_index"] <= 100).all()

    def test_all_departments_present(self, snapshots):
        from config.settings import DEPARTMENTS
        for dept in DEPARTMENTS:
            assert dept in snapshots["department"].values, f"{dept} missing"

    def test_near_miss_rate_positive(self, snapshots):
        assert (snapshots["near_miss_rate"] >= 0).all()

    def test_lti_target_binary(self, snapshots):
        assert set(snapshots["lti_next_30_days"].unique()).issubset({0, 1})

    def test_positive_rate_realistic(self, snapshots):
        pos_rate = snapshots["lti_next_30_days"].mean() * 100
        assert 5 <= pos_rate <= 50, f"Positive rate {pos_rate:.1f}% outside realistic range"

    def test_training_compliance_range(self, snapshots):
        assert (snapshots["training_compliance_pct"] >= 0).all()
        assert (snapshots["training_compliance_pct"] <= 100).all()

    def test_inspection_score_range(self, snapshots):
        assert (snapshots["inspection_score"] >= 0).all()
        assert (snapshots["inspection_score"] <= 100).all()


class TestModel:
    def test_model_artifacts_exist(self):
        from pathlib import Path
        assert (Path("models/artifacts/hsip_model.pkl")).exists()
        assert (Path("models/artifacts/model_metadata.json")).exists()

    def test_model_metadata(self):
        from models.predictor import load_model_metadata
        meta = load_model_metadata()
        assert "roc_auc" in meta
        assert meta["roc_auc"] >= 0.5, "ROC-AUC below random baseline"
        assert "feature_count" in meta
        assert meta["feature_count"] > 0

    def test_score_all_departments(self):
        from models.predictor import score_all_departments
        scores = score_all_departments()
        assert len(scores) == 11
        assert "lti_probability_30d" in scores.columns
        assert (scores["lti_probability_30d"] >= 0).all()
        assert (scores["lti_probability_30d"] <= 1).all()

    def test_risk_levels_valid(self):
        from models.predictor import score_all_departments
        scores = score_all_departments()
        valid = {"Critical","High","Medium","Low"}
        assert set(scores["risk_level"].unique()).issubset(valid)


class TestDataAccess:
    def test_get_latest_week(self):
        from dashboards.data_access import get_latest_week_all_depts
        df = get_latest_week_all_depts()
        assert len(df) == 11

    def test_get_facility_summary(self):
        from dashboards.data_access import get_facility_sci_summary
        s = get_facility_sci_summary()
        required = ["avg_sci","worst_dept","best_dept","total_ltis_ytd",
                    "avg_training_compliance","high_risk_depts"]
        for k in required:
            assert k in s, f"Missing key: {k}"

    def test_get_dept_trend(self):
        from dashboards.data_access import get_dept_trend
        df = get_dept_trend("Drilling")
        assert len(df) > 0
        assert "safety_culture_index" in df.columns

    def test_get_monthly_sci(self):
        from dashboards.data_access import get_monthly_sci
        df = get_monthly_sci()
        assert len(df) > 0
        assert "avg_sci" in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
