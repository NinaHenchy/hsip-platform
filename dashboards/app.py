"""
HSIP Platform — HSE Incident Prediction & Safety Culture Intelligence
Main Streamlit Application
Teal/Emerald theme — distinct from ORPMI (blue) and HSEI (red/orange)
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
for _p in [str(_root), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

st.set_page_config(
    page_title="HSIP | Safety Prediction Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-setup on first run (Streamlit Cloud + local)
_db = Path("database/hsip_dev.db")
_model = Path("models/artifacts/hsip_model.pkl")

if not _db.exists():
    with st.spinner("First run — initialising HSIP database (~30 seconds)..."):
        import subprocess
        subprocess.run([sys.executable, "scripts/setup_database.py"], check=True)
    st.rerun()

if not _model.exists():
    with st.spinner("Training prediction model (~20 seconds)..."):
        import subprocess
        subprocess.run([sys.executable, "scripts/train_model.py"], check=True)
    st.rerun()

# Verify model loads correctly — retrain if sklearn version mismatch
try:
    import pickle
    with open(_model, "rb") as f:
        pickle.load(f)
except Exception:
    with st.spinner("Updating prediction model for current environment..."):
        import subprocess
        subprocess.run([sys.executable, "scripts/train_model.py"], check=True)
    st.rerun()

from dashboards.components.ui_components import inject_css, T
inject_css()

# Sidebar — dark teal theme via CSS
with st.sidebar:
    st.markdown(f"""
    <div style="padding:14px 0 10px 0;">
        <div style="font-size:18px;font-weight:900;color:#c8e8e8;">🎯 HSIP</div>
        <div style="font-size:11px;color:#7fb3b3;margin-top:3px;font-weight:600;">
            HSE Incident Prediction &
        </div>
        <div style="font-size:11px;color:#7fb3b3;">
            Safety Culture Intelligence
        </div>
        <div style="font-size:10px;color:#4a8080;margin-top:4px;">
            OPC-Alpha · 2023–2024
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1a4040;margin:6px 0 10px;">', unsafe_allow_html=True)

    st.markdown('<div style="font-size:9px;color:#4a8080;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">Navigation</div>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        options=[
            "🎯  Safety Culture Command Centre",
            "🔮  LTI Prediction Intelligence",
            "📡  Leading Indicators Deep Dive",
            "🔍  Department Safety Intelligence",
            "📊  Correlation Analysis",
            "➕  Data Entry",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<hr style="border-color:#1a4040;margin:12px 0 10px;">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:10px;color:#4a8080;line-height:2.1;">
        <div>📅 Data: Jan 2023 – Dec 2024</div>
        <div>🧠 Model: Gradient Boosting</div>
        <div>📐 Standard: ISO 45001</div>
        <div>👷 11 Departments · 285 workers</div>
        <div style="margin-top:6px;color:#14a085;font-weight:700;">● Prediction Engine Online</div>
    </div>
    """, unsafe_allow_html=True)


if "Command Centre" in page:
    from dashboards.pages.p1_command_centre import render_command_centre
    render_command_centre()
elif "LTI Prediction" in page:
    from dashboards.pages.p2_to_p5 import render_lti_prediction
    render_lti_prediction()
elif "Leading Indicators" in page:
    from dashboards.pages.p2_to_p5 import render_leading_indicators
    render_leading_indicators()
elif "Department Safety" in page:
    from dashboards.pages.p2_to_p5 import render_dept_drilldown
    render_dept_drilldown()
elif "Correlation" in page:
    from dashboards.pages.p2_to_p5 import render_correlation_analysis
    render_correlation_analysis()
elif "Data Entry" in page:
    from dashboards.pages.p_data_entry import render_data_entry
    render_data_entry()
