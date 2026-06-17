"""
HSIP Data Entry — Log real safety observations and interventions.
All entries saved to SQLite and immediately reflected in dashboards.
"""

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent.parent
for _p in [str(_root), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy import text

from dashboards.components.ui_components import (
    inject_css, page_header, section_header, T
)
from config.settings import DEPARTMENTS


def get_engine():
    from database.db_connection import get_engine as _get
    return _get()


def render_data_entry():
    inject_css()
    page_header(
        "Safety Intelligence Data Entry",
        "Log safety observations and interventions — saved to the prediction engine",
        "➕"
    )

    st.info(
        "Entries are saved to the database and factored into the next SCI computation. "
        "Use this to log real safety events or to test how changing leading indicators "
        "affects the department's risk score."
    )

    tab1, tab2, tab3 = st.tabs([
        "👁️ Safety Observation",
        "📊 Weekly Performance Update",
        "⚡ Manual SCI Override",
    ])

    # ── TAB 1: SAFETY OBSERVATION ─────────────────────────────────────
    with tab1:
        section_header("Submit Safety Observation / Near Miss")

        with st.form("obs_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                obs_type = st.selectbox(
                    "Observation Type *",
                    ["Near Miss", "Unsafe Act", "Unsafe Condition",
                     "Good Practice", "Stop Work Authority",
                     "Dropped Object Potential", "Environmental Concern",
                     "Leadership Safety Walk"]
                )
                obs_dept = st.selectbox("Department *", DEPARTMENTS)
                obs_date = st.date_input("Date *", value=date.today())
                pot_sev  = st.selectbox(
                    "Potential Severity",
                    ["Critical", "High", "Medium", "Low"]
                )

            with col2:
                reporter = st.text_input(
                    "Reported By (leave blank to stay anonymous)"
                )
                is_anon = not bool(reporter)
                followup = st.checkbox(
                    "Follow-up required?",
                    value=obs_type in ["Near Miss","Unsafe Act","Stop Work Authority"]
                )
                immediate_action = st.text_area(
                    "Immediate Action Taken",
                    placeholder="What was done to control the hazard immediately?"
                )

            description = st.text_area(
                "Observation Description *",
                placeholder="What did you observe? Be specific about location, task, and hazard."
            )

            submitted = st.form_submit_button(
                "👁️ Submit Observation",
                use_container_width=True,
                type="primary"
            )

            if submitted:
                if not description:
                    st.error("Please provide a description.")
                else:
                    try:
                        engine = get_engine()
                        with engine.connect() as conn:
                            count = conn.execute(
                                text("SELECT COUNT(*) FROM safety_observations_live")
                            ).scalar()
                            obs_num = f"OBS-HSIP-{count+1:04d}"

                            conn.execute(text("""
                                INSERT INTO safety_observations_live (
                                    observation_date, department, observation_type,
                                    description, potential_severity,
                                    reported_by, is_anonymous,
                                    immediate_action, followup_required
                                ) VALUES (
                                    :date, :dept, :type,
                                    :desc, :severity,
                                    :reporter, :anon,
                                    :action, :followup
                                )
                            """), {
                                "date": str(obs_date),
                                "dept": obs_dept,
                                "type": obs_type,
                                "desc": description,
                                "severity": pot_sev,
                                "reporter": reporter or "Anonymous",
                                "anon": int(is_anon),
                                "action": immediate_action,
                                "followup": int(followup),
                            })
                            conn.commit()

                        if obs_type in ["Near Miss","Stop Work Authority"]:
                            st.success(
                                f"✅ **{obs_num}** submitted — Thank you for reporting!\n\n"
                                f"**Type:** {obs_type} | **Dept:** {obs_dept} | "
                                f"**Potential Severity:** {pot_sev}\n\n"
                                f"This near miss report contributes positively to your "
                                f"department's Safety Culture Index."
                            )
                        else:
                            st.success(
                                f"✅ Observation **{obs_num}** saved.\n\n"
                                f"Navigate to **Leading Indicators** to see the update."
                            )

                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── TAB 2: WEEKLY PERFORMANCE UPDATE ─────────────────────────────
    with tab2:
        section_header("Log This Week's Performance Data")
        st.caption(
            "Update any department's leading indicator scores for the current week. "
            "This feeds directly into the SCI calculation and LTI prediction model."
        )

        with st.form("weekly_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                w_dept = st.selectbox("Department *", DEPARTMENTS, key="w_dept")
                w_date = st.date_input("Week Start Date *", value=date.today(), key="w_date")
                nm_count = st.number_input(
                    "Near Miss Reports This Week", min_value=0, max_value=50, value=2
                )
                insp_score = st.slider("Inspection Score", 0, 100, 82)
                insp_count = st.number_input(
                    "Inspections Conducted", min_value=0, max_value=20, value=4
                )

            with col2:
                training_comp = st.slider("Training Compliance %", 0, 100, 88)
                action_closeout = st.slider("Action Close-Out Rate %", 0, 100, 78)
                ptw_issued = st.number_input(
                    "PTW Issued", min_value=0, max_value=100, value=12
                )
                ptw_viol = st.number_input(
                    "PTW Violations", min_value=0, max_value=10, value=0
                )
                toolbox_talks = st.number_input(
                    "Toolbox Talks", min_value=0, max_value=20, value=3
                )

            had_lti = st.checkbox("Did this department have an LTI this week?")

            w_submitted = st.form_submit_button(
                "📊 Save Weekly Update",
                use_container_width=True,
                type="primary"
            )

            if w_submitted:
                try:
                    from config.settings import DEPT_WORKFORCE, SCI_WEIGHTS
                    engine = get_engine()
                    workforce = DEPT_WORKFORCE.get(w_dept, 30)
                    nm_rate   = round(nm_count / workforce * 100, 2)
                    ptw_comp  = round((1 - ptw_viol / max(1, ptw_issued)) * 100, 1)

                    # Compute SCI
                    nm_score  = min(100, nm_rate * 20)
                    sci = round(
                        nm_score       * SCI_WEIGHTS["near_miss_reporting_rate"] +
                        training_comp  * SCI_WEIGHTS["training_compliance_pct"] +
                        insp_score     * SCI_WEIGHTS["inspection_score_avg"] +
                        action_closeout* SCI_WEIGHTS["action_closeout_rate"] +
                        ptw_comp       * SCI_WEIGHTS["ptw_compliance_rate"],
                        1
                    )

                    with engine.connect() as conn:
                        # Check for existing record
                        existing = conn.execute(text("""
                            SELECT COUNT(*) FROM weekly_dept_snapshot
                            WHERE week_start_date = :date AND department = :dept
                        """), {"date": str(w_date), "dept": w_dept}).scalar()

                        if existing > 0:
                            conn.execute(text("""
                                UPDATE weekly_dept_snapshot SET
                                    near_miss_count = :nm, near_miss_rate = :nm_rate,
                                    inspection_score = :insp, inspection_count = :insp_c,
                                    training_compliance_pct = :train,
                                    action_closeout_rate = :action,
                                    ptw_issued = :ptw_i, ptw_violations = :ptw_v,
                                    ptw_compliance_rate = :ptw_comp,
                                    toolbox_talks = :tb, safety_culture_index = :sci,
                                    lti_count = :lti
                                WHERE week_start_date = :date AND department = :dept
                            """), {
                                "nm": nm_count, "nm_rate": nm_rate,
                                "insp": insp_score, "insp_c": insp_count,
                                "train": training_comp, "action": action_closeout,
                                "ptw_i": ptw_issued, "ptw_v": ptw_viol,
                                "ptw_comp": ptw_comp, "tb": toolbox_talks,
                                "sci": sci, "lti": int(had_lti),
                                "date": str(w_date), "dept": w_dept,
                            })
                            action = "updated"
                        else:
                            from config.settings import DEPT_WORKFORCE
                            conn.execute(text("""
                                INSERT INTO weekly_dept_snapshot (
                                    week_start_date, week_number, year, department,
                                    workforce_size, near_miss_count, near_miss_rate,
                                    inspection_score, inspection_count,
                                    training_compliance_pct, action_closeout_rate,
                                    ptw_issued, ptw_violations, ptw_compliance_rate,
                                    toolbox_talks, safety_culture_index,
                                    lti_count, manhours
                                ) VALUES (
                                    :date, :wk, :yr, :dept,
                                    :wf, :nm, :nm_rate,
                                    :insp, :insp_c,
                                    :train, :action,
                                    :ptw_i, :ptw_v, :ptw_comp,
                                    :tb, :sci,
                                    :lti, :manhours
                                )
                            """), {
                                "date": str(w_date),
                                "wk": w_date.isocalendar()[1],
                                "yr": w_date.year,
                                "dept": w_dept,
                                "wf": workforce,
                                "nm": nm_count, "nm_rate": nm_rate,
                                "insp": insp_score, "insp_c": insp_count,
                                "train": training_comp, "action": action_closeout,
                                "ptw_i": ptw_issued, "ptw_v": ptw_viol,
                                "ptw_comp": ptw_comp, "tb": toolbox_talks,
                                "sci": sci, "lti": int(had_lti),
                                "manhours": workforce * 12 * 14 * 0.85,
                            })
                            action = "saved"
                        conn.commit()

                    sci_color = (
                        "🟢" if sci >= 70 else
                        "🟡" if sci >= 55 else "🔴"
                    )
                    st.success(
                        f"✅ Weekly data {action} for **{w_dept}**\n\n"
                        f"**Computed SCI:** {sci_color} {sci}/100\n\n"
                        f"**Near Miss Rate:** {nm_rate:.2f} per 100 workers\n\n"
                        f"Navigate to **Command Centre** to see the updated SCI gauge."
                    )

                except Exception as e:
                    st.error(f"Error: {e}")

    # ── TAB 3: MANUAL SCI NOTE ────────────────────────────────────────
    with tab3:
        section_header("What-If: SCI Sensitivity Calculator")
        st.caption(
            "Explore how changing individual leading indicators would affect "
            "a department's Safety Culture Index. This is a calculator only — "
            "it does not save to the database."
        )

        from config.settings import SCI_WEIGHTS
        col1, col2 = st.columns(2)

        with col1:
            calc_dept = st.selectbox("Department", DEPARTMENTS, key="calc_dept")
            nm_rate_calc = st.slider("Near Miss Rate (per 100/wk)", 0.0, 10.0, 2.5, 0.1)
            train_calc   = st.slider("Training Compliance %", 0, 100, 85)

        with col2:
            insp_calc    = st.slider("Inspection Score", 0, 100, 80)
            action_calc  = st.slider("Action Close-Out %", 0, 100, 75)
            ptw_calc     = st.slider("PTW Compliance %", 0, 100, 95)

        nm_score_c = min(100, nm_rate_calc * 20)
        sci_calc = round(
            nm_score_c   * SCI_WEIGHTS["near_miss_reporting_rate"] +
            train_calc   * SCI_WEIGHTS["training_compliance_pct"] +
            insp_calc    * SCI_WEIGHTS["inspection_score_avg"] +
            action_calc  * SCI_WEIGHTS["action_closeout_rate"] +
            ptw_calc     * SCI_WEIGHTS["ptw_compliance_rate"],
            1
        )
        from dashboards.components.ui_components import sci_gauge_color
        color = sci_gauge_color(sci_calc)
        label = (
            "Excellent ✅" if sci_calc >= 85 else
            "Good 🟢"      if sci_calc >= 70 else
            "Fair 🟡"      if sci_calc >= 55 else
            "Poor 🔴 — High LTI Risk"
        )

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}15,{T['card']});
                     border:2px solid {color};border-radius:12px;
                     padding:20px;text-align:center;margin-top:16px;">
            <div style="font-size:11px;color:{T['text_sub']};text-transform:uppercase;">
                Computed Safety Culture Index
            </div>
            <div style="font-size:56px;font-weight:900;color:{color};line-height:1.1;">
                {sci_calc}
            </div>
            <div style="font-size:14px;font-weight:700;color:{color};">{label}</div>
            <div style="font-size:11px;color:{T['text_muted']};margin-top:6px;">
                Adjust sliders above to see how each indicator affects the SCI
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RECENT LIVE OBSERVATIONS ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Recent Live Safety Observations")
    try:
        engine = get_engine()
        df = pd.read_sql("""
            SELECT observation_date, department, observation_type,
                   potential_severity, reported_by, description
            FROM safety_observations_live
            ORDER BY rowid DESC LIMIT 10
        """, engine)
        if not df.empty:
            df["description"] = df["description"].str[:80]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No live observations logged yet. Use Tab 1 above to submit one.")
    except Exception:
        pass
