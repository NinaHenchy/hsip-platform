"""
Page 1 — Safety Culture Command Centre
Hero page: SCI gauges per department, facility overview, risk alert summary.
"""

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent.parent
for _p in [str(_root), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from dashboards.data_access import (
    get_latest_week_all_depts, get_facility_sci_summary,
    get_monthly_sci, get_lti_events
)
from dashboards.components.ui_components import (
    inject_css, page_header, section_header, alert_banner,
    apply_layout, sci_gauge_color, T, RISK_COLORS, DEPT_COLORS
)
from config.settings import FACILITY_NAME, SCI_THRESHOLDS


def render_command_centre():
    inject_css()
    page_header(
        "Safety Culture Command Centre",
        f"{FACILITY_NAME} · Department Safety Intelligence · Live Dashboard",
        "🎯"
    )

    summary = get_facility_sci_summary()
    latest  = get_latest_week_all_depts()
    monthly = get_monthly_sci()
    lti     = get_lti_events()

    if not summary or latest.empty:
        st.error("No data. Run setup_database.py first.")
        return

    # ── ALERTS ────────────────────────────────────────────────────────
    high_risk = latest[latest["safety_culture_index"] < 60]
    if not high_risk.empty:
        depts = ", ".join(high_risk["department"].tolist())
        alert_banner(
            f"⚠️ {len(high_risk)} department(s) with SCI below 60: {depts}. "
            "Immediate HSE management attention required.",
            "critical"
        )

    # ── FACILITY KPIs ─────────────────────────────────────────────────
    section_header("Facility Safety Culture Index — Current Status")

    sci_color = sci_gauge_color(summary["avg_sci"])
    sci_label = (
        "Excellent" if summary["avg_sci"] >= SCI_THRESHOLDS["excellent"] else
        "Good"      if summary["avg_sci"] >= SCI_THRESHOLDS["good"] else
        "Fair"      if summary["avg_sci"] >= SCI_THRESHOLDS["fair"] else
        "Poor — Intervention Required"
    )

    # Hero SCI card
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{T['primary']}15 0%,{T['card']} 100%);
                border:2px solid {sci_color};border-radius:14px;
                padding:20px 30px;text-align:center;margin-bottom:20px;">
        <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.18em;
                    color:{T['text_sub']};font-weight:700;">
            Facility Safety Culture Index — All Departments
        </div>
        <div style="font-size:68px;font-weight:900;color:{sci_color};line-height:1.05;margin:8px 0;">
            {summary["avg_sci"]}
        </div>
        <div style="font-size:14px;font-weight:700;color:{sci_color};">{sci_label}</div>
        <div style="font-size:11px;color:{T['text_muted']};margin-top:4px;">
            Composite: Near Miss Reporting · Training · Inspections · Actions · PTW
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Departments Monitored", summary["dept_count"])
    with c2: st.metric("High Risk Departments", summary["high_risk_depts"],
                        "SCI < 65", delta_color="inverse")
    with c3: st.metric("LTI Events (2yr)", summary["total_ltis_ytd"])
    with c4: st.metric("Avg Training Compliance", f"{summary['avg_training_compliance']}%")
    with c5: st.metric("Avg Inspection Score", f"{summary['avg_inspection_score']}/100")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SCI GAUGES PER DEPARTMENT ─────────────────────────────────────
    section_header("Safety Culture Index — All Departments")

    cols = st.columns(4)
    for i, (_, row) in enumerate(latest.iterrows()):
        sci   = float(row["safety_culture_index"])
        color = sci_gauge_color(sci)
        dept  = row["department"]
        short = dept.replace("Contractor — ","C/")

        with cols[i % 4]:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sci,
                number=dict(font=dict(size=22, color=color, family="sans-serif"),
                            suffix=""),
                gauge=dict(
                    axis=dict(range=[0,100], tickfont=dict(size=8),
                              tickcolor=T["text_muted"]),
                    bar=dict(color=color, thickness=0.30),
                    bgcolor=T["card_teal"],
                    borderwidth=2, bordercolor=T["border"],
                    steps=[
                        dict(range=[0,40],  color="rgba(192,57,43,0.08)"),
                        dict(range=[40,55], color="rgba(230,126,34,0.08)"),
                        dict(range=[55,70], color="rgba(240,165,0,0.08)"),
                        dict(range=[70,85], color="rgba(13,115,119,0.08)"),
                        dict(range=[85,100],color="rgba(26,138,90,0.12)"),
                    ],
                    threshold=dict(
                        line=dict(color=T["text"], width=2),
                        thickness=0.75, value=70
                    ),
                ),
            ))
            fig_g.update_layout(
                height=170, margin=dict(l=10,r=10,t=15,b=5),
                paper_bgcolor=T["plotly_paper"],
                font=dict(color=T["text"]),
            )
            st.plotly_chart(fig_g, use_container_width=True, key=f"p1_gauge_{i}")
            nm_rate = float(row.get("near_miss_rate", 0))
            nm_color = T["good"] if nm_rate >= 3 else T["warning"] if nm_rate >= 1.5 else T["danger"]
            st.markdown(f"""
            <div style="text-align:center;margin-top:-14px;margin-bottom:12px;">
                <div style="font-size:11px;font-weight:700;color:{T['text']};
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {short}
                </div>
                <div style="font-size:10px;color:{nm_color};">
                    NM Rate: {nm_rate:.1f}/100
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SCI TREND ─────────────────────────────────────────────────────
    section_header("Safety Culture Index Trend — All Departments (Monthly Average)")

    if not monthly.empty:
        monthly["year_month"] = monthly["year_month"].astype(str)
        pivot = monthly.pivot_table(
            index="year_month", columns="department",
            values="avg_sci", aggfunc="mean"
        ).reset_index()

        fig_trend = go.Figure()
        for j, dept in enumerate(DEPARTMENTS if "DEPARTMENTS" in dir() else pivot.columns[1:]):
            col = dept if dept in pivot.columns else None
            if col is None:
                continue
            color = DEPT_COLORS[j % len(DEPT_COLORS)]
            fig_trend.add_trace(go.Scatter(
                x=pivot["year_month"], y=pivot[col],
                mode="lines", name=col.replace("Contractor — ","C/"),
                line=dict(color=color, width=1.8),
                opacity=0.85,
            ))

        fig_trend.add_hline(y=SCI_THRESHOLDS["good"], line_dash="dash",
                            line_color=T["primary"], line_width=1.5,
                            annotation_text="Good 70",
                            annotation_font=dict(size=9, color=T["primary"]))
        fig_trend.add_hline(y=SCI_THRESHOLDS["fair"], line_dash="dot",
                            line_color=T["warning"], line_width=1.2,
                            annotation_text="Fair 55",
                            annotation_font=dict(size=9, color=T["warning"]))
        apply_layout(fig_trend, height=360)
        fig_trend.update_layout(
            yaxis=dict(title="Safety Culture Index", range=[30,105]),
            legend=dict(orientation="h", y=-0.25, x=0, font=dict(size=9)),
            margin=dict(l=55,r=80,t=20,b=100),
        )
        st.plotly_chart(fig_trend, use_container_width=True, key="p1_command_centre_chart_2")

    # ── DEPT RANKING TABLE ────────────────────────────────────────────
    section_header("Department Safety Ranking — Current Week")

    display = latest[[
        "department","safety_culture_index","near_miss_rate",
        "training_compliance_pct","inspection_score",
        "action_closeout_rate","lti_count"
    ]].copy()
    display.columns = ["Department","SCI","NM Rate","Training %","Insp Score","Action Close%","LTI"]
    display["SCI"]      = display["SCI"].round(1)
    display["NM Rate"]  = display["NM Rate"].round(2)
    display["Training %"] = display["Training %"].round(1)
    display["Insp Score"] = display["Insp Score"].round(1)
    display["Action Close%"] = display["Action Close%"].round(1)
    st.dataframe(display, use_container_width=True, hide_index=True, height=320)
    st.caption("Sorted by Safety Culture Index ascending (lowest performing first).")
