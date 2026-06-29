"""
HSIP Platform — HSE Incident Prediction & Safety Culture Intelligence
Inline setup — no subprocess — works on Streamlit Cloud, Docker, Local
Deep Teal Slate Theme
"""

import sys
import os
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
for _p in [str(_root), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

st.set_page_config(
    page_title="HSIP | Safety Culture & LTI Prediction Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

_db    = _root / "database" / "hsip_dev.db"
_model = _root / "models" / "artifacts" / "hsip_model.pkl"

def _setup_db():
    os.makedirs(str(_root / "database"), exist_ok=True)
    os.makedirs(str(_root / "logs"), exist_ok=True)
    os.makedirs(str(_root / "data" / "raw"), exist_ok=True)
    os.makedirs(str(_root / "data" / "processed"), exist_ok=True)
    os.makedirs(str(_root / "models" / "artifacts"), exist_ok=True)
    from database.db_connection import initialize_database
    initialize_database()
    from etl.extractors.synthetic_data_generator import run_full_generation
    from etl.loaders.db_loader import load_all_tables
    from database.db_connection import get_engine
    data   = run_full_generation()
    engine = get_engine()
    load_all_tables(data, engine)

def _train():
    from models.predictor import train_model
    train_model()

def _db_has_data():
    try:
        from sqlalchemy import text
        from database.db_connection import get_engine
        with get_engine().connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM weekly_dept_snapshot")).scalar()
        return count > 0
    except Exception:
        return False

if not _db.exists():
    with st.spinner("First run — initialising HSIP database (~60 seconds)..."):
        try:
            _setup_db()
        except Exception as e:
            st.error(f"Database setup failed: {e}")
            st.exception(e)
            st.stop()
    st.rerun()

if not _db_has_data():
    with st.spinner("Loading safety data (~60 seconds)..."):
        try:
            _setup_db()
        except Exception as e:
            st.error(f"Data load failed: {e}")
            st.exception(e)
            st.stop()
    st.rerun()

if not _model.exists():
    with st.spinner("Training LTI prediction model (~30 seconds)..."):
        try:
            _train()
        except Exception as e:
            st.error(f"Model training failed: {e}")
            st.exception(e)
            st.stop()
    st.rerun()

try:
    import pickle
    with open(_model, "rb") as _f:
        pickle.load(_f)
except Exception:
    with st.spinner("Updating prediction model..."):
        try:
            _train()
        except Exception as e:
            st.error(f"Model update failed: {e}")
            st.exception(e)
            st.stop()
    st.rerun()

from dashboards.components.ui_components import inject_css
inject_css()

with st.sidebar:
    st.markdown("""
    <div style="padding:12px 0 8px 0;">
        <div style="font-size:16px;font-weight:700;color:#00b4d8;">🎯 HSIP Platform</div>
        <div style="font-size:11px;color:#7aaab8;margin-top:3px;">
            Safety Culture &amp; LTI Prediction
        </div>
        <div style="font-size:10px;color:#3d6070;margin-top:2px;">
            Offshore Production Complex · OPC-Alpha
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1e3d47;margin:6px 0 12px;">', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        options=[
            "🎯  Safety Culture Command Centre",
            "📊  Department Analysis",
            "🔮  LTI Prediction Intelligence",
            "📈  SCI Trend Analysis",
            "🎓  Training & Competency Intel",
            "➕  Data Entry",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<hr style="border-color:#1e3d47;margin:12px 0 10px;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#7aaab8;line-height:2.1;">
        <div>📅 Data Period: Jan–Dec 2024</div>
        <div>🤖 Gradient Boosting + Isotonic</div>
        <div>📐 ISO 45001 · Leading Indicators</div>
        <div style="margin-top:6px;color:#06d6a0;font-weight:600;">● Platform Online</div>
    </div>
    """, unsafe_allow_html=True)

if "Command Centre" in page:
    from dashboards.pages.p1_command_centre import render_command_centre
    render_command_centre()
elif "Department Analysis" in page:
    from dashboards.pages.p2_to_p5 import render_dept_drilldown
    render_dept_drilldown()
elif "LTI Prediction" in page:
    from dashboards.pages.p2_to_p5 import render_lti_prediction
    render_lti_prediction()
elif "SCI Trend" in page:
    from dashboards.pages.p2_to_p5 import render_leading_indicators
    render_leading_indicators()
elif "Training" in page:
    from dashboards.pages.p2_to_p5 import render_correlation_analysis
    render_correlation_analysis()
elif "Data Entry" in page:
    from dashboards.pages.p_data_entry import render_data_entry
    render_data_entry()