"""
HSIP Pages 2-5
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
import numpy as np

from dashboards.data_access import (
    get_latest_week_all_depts, get_weekly_snapshots,
    get_monthly_sci, get_lti_events, get_dept_trend,
    get_facility_sci_summary
)
from dashboards.components.ui_components import (
    inject_css, page_header, section_header, alert_banner,
    apply_layout, sci_gauge_color, T, RISK_COLORS, DEPT_COLORS, SCI_COLORS, DEPT_COLOR_LIST
)
from config.settings import DEPARTMENTS, SCI_THRESHOLDS, SCI_WEIGHTS


# ═══════════════════════════════════════════════════════════════
# PAGE 2 — LTI PREDICTION INTELLIGENCE
# ═══════════════════════════════════════════════════════════════
def render_lti_prediction():
    inject_css()
    page_header(
        "LTI Prediction Intelligence",
        "30-Day Lost Time Injury probability per department · ML-powered · Gradient Boosting",
        "🔮"
    )

    # Load ML scores
    try:
        from models.predictor import (
            score_all_departments, load_model_metadata,
            load_feature_importance, get_top_risk_factor
        )
        scores   = score_all_departments()
        metadata = load_model_metadata()
        fi_df    = load_feature_importance()
        ml_ok    = True
    except Exception as e:
        ml_ok = False
        scores = pd.DataFrame()
        metadata = {}
        fi_df = pd.DataFrame()
        st.warning(f"ML model not available: {e}. Run `python scripts/train_model.py`")

    latest = get_latest_week_all_depts()

    # ── MODEL BANNER ──────────────────────────────────────────────────
    if ml_ok and metadata:
        roc  = metadata.get("roc_auc", 0)
        rec  = metadata.get("recall", 0)
        prec = metadata.get("precision", 0)
        f1   = metadata.get("f1", 0)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{T['primary']}18 0%,{T['card']} 100%);
                     border:1px solid {T['primary']};border-left:5px solid {T['primary']};
                     border-radius:10px;padding:14px 22px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;align-items:center;">
                <div>
                    <div style="font-size:11px;color:{T['text_sub']};text-transform:uppercase;letter-spacing:0.1em;">
                        Predictive Model Status
                    </div>
                    <div style="font-size:14px;font-weight:800;color:{T['primary']};margin-top:3px;">
                        ● {metadata.get('model_type','Gradient Boosting')} · Predicting 30-Day LTI Risk
                    </div>
                    <div style="font-size:11px;color:{T['text_muted']};margin-top:2px;">
                        {metadata.get('feature_count',0)} features · {metadata.get('training_rows',0):,} training records · Temporal validation
                    </div>
                </div>
                <div style="display:flex;gap:28px;">
                    {"".join([f'<div style="text-align:center;"><div style="font-size:9px;color:{T["text_muted"]};text-transform:uppercase;">{k}</div><div style="font-size:20px;font-weight:800;color:{T["primary"]};">{v:.4f}</div></div>' for k,v in [("ROC-AUC",roc),("Precision",prec),("Recall",rec),("F1",f1)]])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── PREDICTION CARDS ──────────────────────────────────────────────
    section_header("30-Day LTI Probability — All Departments")

    if ml_ok and not scores.empty:
        # Alert for high risk depts
        critical = scores[scores["risk_level"] == "Critical"]
        high     = scores[scores["risk_level"] == "High"]
        if not critical.empty:
            depts = ", ".join(critical["department"].tolist())
            alert_banner(f"CRITICAL LTI RISK: {depts} — immediate intervention required.", "critical")
        if not high.empty:
            depts = ", ".join(high["department"].tolist())
            alert_banner(f"HIGH LTI RISK: {depts} — enhanced monitoring and targeted action needed.", "warning")

        for _, row in scores.iterrows():
            prob  = float(row["lti_probability_30d"])
            risk  = row["risk_level"]
            color = RISK_COLORS.get(risk, T["primary"])
            sci   = float(row.get("sci_score", 0))
            dept  = row["department"]

            # Top risk factor
            risk_factor = get_top_risk_factor(dept, scores) if ml_ok else ""

            bar_pct = int(prob * 100)
            st.markdown(f"""
            <div style="background:{T['card']};border:1px solid {color}55;
                         border-left:5px solid {color};border-radius:10px;
                         padding:14px 20px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;
                             align-items:center;flex-wrap:wrap;gap:10px;">
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:13px;font-weight:800;color:{T['text']};">
                            {dept}
                        </div>
                        <div style="font-size:11px;color:{T['text_muted']};margin-top:2px;">
                            SCI: {sci:.0f} · {risk_factor}
                        </div>
                        <div style="margin-top:8px;background:{T['grid']};border-radius:4px;height:6px;">
                            <div style="background:{color};width:{bar_pct}%;height:6px;border-radius:4px;"></div>
                        </div>
                    </div>
                    <div style="display:flex;gap:20px;align-items:center;">
                        <div style="text-align:center;">
                            <div style="font-size:9px;color:{T['text_muted']};text-transform:uppercase;">30-Day LTI Prob</div>
                            <div style="font-size:24px;font-weight:900;color:{color};">{prob*100:.0f}%</div>
                        </div>
                        <span style="font-size:11px;font-weight:700;padding:4px 12px;
                               border-radius:5px;color:{color};background:{color}22;
                               border:1px solid {color}55;">
                            {risk}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── FEATURE IMPORTANCE ─────────────────────────────────────────
        col_fi, col_risk = st.columns(2)

        with col_fi:
            section_header("Top Predictive Features — What Drives LTI Risk")
            if not fi_df.empty:
                top15 = fi_df.head(15).sort_values("importance_pct", ascending=True)

                def _color(f):
                    if "sci" in f:      return T["primary"]
                    if "near_miss" in f: return T["secondary"]
                    if "training" in f: return T["accent"]
                    if "inspection" in f: return T["good"]
                    if "action" in f:   return T["warning"]
                    return T["text_muted"]

                fig_fi = go.Figure(go.Bar(
                    x=top15["importance_pct"], y=top15["feature"],
                    orientation="h",
                    marker_color=[_color(f) for f in top15["feature"]],
                    text=[f"{v:.1f}%" for v in top15["importance_pct"]],
                    textposition="outside", textfont=dict(size=9),
                ))
                apply_layout(fig_fi, height=380)
                fig_fi.update_layout(
                    xaxis_title="Feature Importance %",
                    margin=dict(l=230,r=50,t=20,b=40),
                    showlegend=False,
                )
                st.plotly_chart(fig_fi, use_container_width=True, key="p2_to_p5_chart_1")

        with col_risk:
            section_header("Risk Level Distribution")
            risk_counts = scores["risk_level"].value_counts()
            fig_risk = go.Figure(go.Pie(
                labels=risk_counts.index.tolist(),
                values=risk_counts.values.tolist(),
                marker_colors=[RISK_COLORS.get(r, T["primary"]) for r in risk_counts.index],
                hole=0.55,
                textinfo="label+value+percent",
                textfont=dict(size=12),
            ))
            apply_layout(fig_risk, height=280)
            fig_risk.update_layout(showlegend=False, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig_risk, use_container_width=True, key="p2_to_p5_chart_2")

            st.markdown("<br>", unsafe_allow_html=True)
            section_header("Prediction Table")
            pred_display = scores[[
                "department","lti_probability_30d","risk_level",
                "sci_score","training_compliance","inspection_score"
            ]].copy()
            pred_display.columns = ["Department","LTI Prob","Risk","SCI","Training%","Inspection"]
            pred_display["LTI Prob"] = pred_display["LTI Prob"].apply(lambda x: f"{x*100:.0f}%")
            pred_display["SCI"] = pred_display["SCI"].round(0)
            pred_display["Training%"] = pred_display["Training%"].round(1)
            pred_display["Inspection"] = pred_display["Inspection"].round(1)
            st.dataframe(pred_display, use_container_width=True, hide_index=True)
    else:
        st.info("Run `python scripts/train_model.py` to generate LTI predictions.")


# ═══════════════════════════════════════════════════════════════
# PAGE 3 — LEADING INDICATORS DEEP DIVE
# ═══════════════════════════════════════════════════════════════
def render_leading_indicators():
    inject_css()
    page_header(
        "Leading Indicators Deep Dive",
        "Near Miss Reporting · Training Compliance · PTW · SWA · Action Close-Out",
        "📡"
    )

    latest  = get_latest_week_all_depts()
    monthly = get_monthly_sci()
    summary = get_facility_sci_summary()

    section_header("SCI Component Breakdown — All Departments (Current Week)")

    if not latest.empty:
        c1, c2, c3, c4, c5 = st.columns(5)
        metrics = [
            (c1, "Avg Near Miss Rate", f"{latest['near_miss_rate'].mean():.2f}", "/100 workers/wk",
             "Target: >3.0 (higher = better reporting culture)"),
            (c2, "Avg Training Compliance", f"{latest['training_compliance_pct'].mean():.1f}%", "",
             "Target: >90%"),
            (c3, "Avg Inspection Score", f"{latest['inspection_score'].mean():.1f}", "/100",
             "Target: >80"),
            (c4, "Avg Action Close-Out", f"{latest['action_closeout_rate'].mean():.1f}%", "",
             "Target: >85%"),
            (c5, "Avg PTW Compliance", f"{latest['ptw_compliance_rate'].mean():.1f}%", "",
             "Target: >98%"),
        ]
        for col, label, val, unit, tip in metrics:
            with col:
                st.metric(label, f"{val}{unit}", help=tip)

        st.markdown("<br>", unsafe_allow_html=True)

        # Near Miss Rate — bar chart (higher = better)
        col_l, col_r = st.columns(2)
        with col_l:
            section_header("Near Miss Reporting Rate — Higher is Better")
            nm_sorted = latest.sort_values("near_miss_rate", ascending=True)
            nm_colors = [
                T["good"] if v >= 3 else T["primary"] if v >= 1.5 else T["danger"]
                for v in nm_sorted["near_miss_rate"]
            ]
            fig_nm = go.Figure(go.Bar(
                x=nm_sorted["near_miss_rate"],
                y=nm_sorted["department"].str.replace("Contractor — ","C/"),
                orientation="h",
                marker_color=nm_colors,
                text=[f"{v:.2f}" for v in nm_sorted["near_miss_rate"]],
                textposition="outside",
            ))
            fig_nm.add_vline(x=3.0, line_dash="dash", line_color=T["good"],
                             line_width=1.5, annotation_text="Target 3.0",
                             annotation_font=dict(size=9, color=T["good"]))
            apply_layout(fig_nm, height=300)
            fig_nm.update_layout(margin=dict(l=140,r=50,t=20,b=40), showlegend=False,
                                 xaxis_title="Near Misses per 100 Workers per Week")
            st.plotly_chart(fig_nm, use_container_width=True, key="p2_to_p5_chart_3")

        with col_r:
            section_header("Training Compliance by Department")
            tr_sorted = latest.sort_values("training_compliance_pct", ascending=True)
            tr_colors = [
                T["good"] if v >= 90 else T["primary"] if v >= 80 else T["danger"]
                for v in tr_sorted["training_compliance_pct"]
            ]
            fig_tr = go.Figure(go.Bar(
                x=tr_sorted["training_compliance_pct"],
                y=tr_sorted["department"].str.replace("Contractor — ","C/"),
                orientation="h",
                marker_color=tr_colors,
                text=[f"{v:.0f}%" for v in tr_sorted["training_compliance_pct"]],
                textposition="outside",
            ))
            fig_tr.add_vline(x=90, line_dash="dash", line_color=T["good"],
                             line_width=1.5, annotation_text="Target 90%",
                             annotation_font=dict(size=9, color=T["good"]))
            apply_layout(fig_tr, height=300)
            fig_tr.update_layout(margin=dict(l=140,r=50,t=20,b=40), showlegend=False,
                                 xaxis_title="Training Compliance %")
            st.plotly_chart(fig_tr, use_container_width=True, key="p2_to_p5_chart_4")

        # SCI Weights explanation
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Safety Culture Index Composition")
        st.info(
            "The **Safety Culture Index (SCI)** is a composite score (0–100) "
            "computed from 5 leading indicators with the following weights:\n\n"
            f"- Near Miss Reporting Rate: **{SCI_WEIGHTS['near_miss_reporting_rate']*100:.0f}%** — "
            "High reporting = healthy culture where workers feel safe to speak up\n\n"
            f"- Training Compliance: **{SCI_WEIGHTS['training_compliance_pct']*100:.0f}%** — "
            "Competent workforce reduces human factor incidents\n\n"
            f"- Inspection Score: **{SCI_WEIGHTS['inspection_score_avg']*100:.0f}%** — "
            "Physical workplace conditions reflect management commitment\n\n"
            f"- Action Close-Out Rate: **{SCI_WEIGHTS['action_closeout_rate']*100:.0f}%** — "
            "Following through on actions shows the system works\n\n"
            f"- PTW Compliance: **{SCI_WEIGHTS['ptw_compliance_rate']*100:.0f}%** — "
            "Permit discipline prevents major process safety events"
        )

        # Radar chart of SCI components per top 4 depts
        section_header("Leading Indicator Radar — Top 4 Highest Risk Departments")
        bottom4 = latest.nsmallest(4, "safety_culture_index")
        categories = ["Near Miss Rate", "Training %", "Inspection", "Action Close%", "PTW %"]

        fig_radar = go.Figure()
        for j, (_, row) in enumerate(bottom4.iterrows()):
            vals = [
                min(100, row["near_miss_rate"] * 20),
                row["training_compliance_pct"],
                row["inspection_score"],
                row["action_closeout_rate"],
                row["ptw_compliance_rate"],
            ]
            cats_c = categories + [categories[0]]
            vals_c = vals + [vals[0]]
            color  = DEPT_COLORS[j]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_c, theta=cats_c,
                fill="toself",
                fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)",
                line=dict(color=color, width=2),
                name=row["department"].replace("Contractor — ","C/"),
                marker=dict(size=6),
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,110],
                                tickfont=dict(size=9, color=T["text_muted"]),
                                gridcolor=T["grid"]),
                angularaxis=dict(tickfont=dict(size=10, color=T["text_sub"]),
                                 linecolor=T["border"]),
                bgcolor=T["card_teal"],
            ),
            paper_bgcolor=T["plotly_paper"],
            font=dict(color=T["text"]),
            height=380, showlegend=True,
            legend=dict(orientation="h", y=-0.15, x=0, font=dict(size=10)),
            margin=dict(l=40,r=40,t=20,b=80),
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="p2_to_p5_chart_5")


# ═══════════════════════════════════════════════════════════════
# PAGE 4 — DEPARTMENT DRILL-DOWN
# ═══════════════════════════════════════════════════════════════
def render_dept_drilldown():
    inject_css()
    page_header(
        "Department Safety Intelligence",
        "Select any department for full safety culture history and LTI correlation analysis",
        "🔍"
    )

    selected = st.selectbox(
        "Select Department",
        options=DEPARTMENTS,
        index=0,
    )

    trend = get_dept_trend(selected)
    latest = get_latest_week_all_depts()
    lti = get_lti_events()

    if trend.empty:
        st.warning("No data for this department.")
        return

    trend["week_start_date"] = pd.to_datetime(trend["week_start_date"])
    dept_lti = lti[lti["department"] == selected] if not lti.empty else pd.DataFrame()
    dept_latest = latest[latest["department"] == selected]

    # KPI row
    if not dept_latest.empty:
        row = dept_latest.iloc[0]
        sci = float(row["safety_culture_index"])
        color = sci_gauge_color(sci)
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{color}18,{T['card']});
                         border:2px solid {color};border-radius:10px;
                         padding:14px;text-align:center;">
                <div style="font-size:10px;color:{T['text_sub']};text-transform:uppercase;">SCI Score</div>
                <div style="font-size:36px;font-weight:900;color:{color};">{sci:.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2: st.metric("Near Miss Rate", f"{row['near_miss_rate']:.2f}", "/100/wk")
        with c3: st.metric("Training %", f"{row['training_compliance_pct']:.0f}%")
        with c4: st.metric("Inspection Score", f"{row['inspection_score']:.0f}/100")
        with c5: st.metric("LTI Count (all time)", len(dept_lti))

    st.markdown("<br>", unsafe_allow_html=True)

    # SCI over time with LTI markers
    section_header(f"Safety Culture Index — {selected} — Full History")
    fig_sci = go.Figure()
    fig_sci.add_trace(go.Scatter(
        x=trend["week_start_date"], y=trend["safety_culture_index"],
        mode="lines", name="SCI",
        line=dict(color=T["primary"], width=2.5),
        fill="tozeroy", fillcolor='rgba(13,115,119,0.06)',
    ))

    # Mark LTI events
    if not dept_lti.empty:
        for _, lrow in dept_lti.iterrows():
            fig_sci.add_vline(
                x=str(lrow["event_date"]),
                line_dash="dot", line_color=T["danger"],
                line_width=1.5, opacity=0.8,
            )

    for y_val, label, clr in [
        (SCI_THRESHOLDS["excellent"], "Excellent 85", T["good"]),
        (SCI_THRESHOLDS["good"],      "Good 70",      T["primary"]),
        (SCI_THRESHOLDS["fair"],      "Fair 55",      T["warning"]),
    ]:
        fig_sci.add_hline(y=y_val, line_dash="dash", line_color=clr,
                          line_width=1, opacity=0.7)

    apply_layout(fig_sci, height=300)
    fig_sci.update_layout(
        yaxis=dict(title="SCI Score", range=[20,105]),
        showlegend=False,
        margin=dict(l=55,r=20,t=20,b=50),
    )
    st.plotly_chart(fig_sci, use_container_width=True, key="p2_to_p5_chart_6")
    st.caption("Red dotted vertical lines mark actual LTI events. Note how SCI tends to decline before LTI events.")

    # Component trends
    section_header("Leading Indicator Components — Weekly Trend")
    col_l, col_r = st.columns(2)

    with col_l:
        fig_comp = go.Figure()
        for col, label, color in [
            ("training_compliance_pct", "Training %", T["secondary"]),
            ("inspection_score",        "Inspection",  T["accent"]),
            ("action_closeout_rate",    "Action Close%", T["good"]),
        ]:
            fig_comp.add_trace(go.Scatter(
                x=trend["week_start_date"], y=trend[col],
                mode="lines", name=label,
                line=dict(width=1.8),
            ))
        apply_layout(fig_comp, "Inspection · Training · Actions", height=260)
        fig_comp.update_layout(
            yaxis=dict(title="%", range=[0,105]),
            legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10)),
            margin=dict(l=55,r=20,t=35,b=50),
        )
        st.plotly_chart(fig_comp, use_container_width=True, key="p2_to_p5_chart_7")

    with col_r:
        fig_nm = go.Figure()
        fig_nm.add_trace(go.Bar(
            x=trend["week_start_date"], y=trend["near_miss_rate"],
            name="Near Miss Rate",
            marker_color=[
                T["good"] if v >= 3 else T["primary"] if v >= 1.5 else T["danger"]
                for v in trend["near_miss_rate"]
            ],
        ))
        fig_nm.add_hline(y=3.0, line_dash="dash", line_color=T["good"],
                          line_width=1.5, annotation_text="Target 3.0",
                          annotation_font=dict(size=9))
        apply_layout(fig_nm, "Near Miss Reporting Rate", height=260)
        fig_nm.update_layout(showlegend=False, yaxis_title="Rate /100/wk",
                             margin=dict(l=55,r=20,t=35,b=50))
        st.plotly_chart(fig_nm, use_container_width=True, key="p2_to_p5_chart_8")

    # LTI Event log
    if not dept_lti.empty:
        section_header(f"LTI Event History — {selected}")
        st.dataframe(dept_lti[["event_date","event_type","severity",
                                "days_lost","root_cause_category","description"]],
                     use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PAGE 5 — CORRELATION ANALYSIS
# ═══════════════════════════════════════════════════════════════
def render_correlation_analysis():
    inject_css()
    page_header(
        "Safety Culture Correlation Analysis",
        "Does SCI actually predict LTIs? Evidence-based analysis of leading vs lagging indicator relationships",
        "📊"
    )

    snapshots = get_weekly_snapshots()
    if snapshots.empty:
        st.warning("No data available.")
        return

    snapshots["week_start_date"] = pd.to_datetime(snapshots["week_start_date"])

    # Key insight box
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{T['primary']}15 0%,{T['card']} 100%);
                 border:2px solid {T['primary']};border-radius:12px;
                 padding:18px 24px;margin-bottom:20px;">
        <div style="font-size:14px;font-weight:800;color:{T['primary']};margin-bottom:8px;">
            🔬 The Core Hypothesis
        </div>
        <div style="font-size:13px;color:{T['text']};line-height:1.7;">
            Safety Culture Index (SCI) measured <strong>today</strong> should predict 
            Lost Time Injuries <strong>30 days from now</strong>. 
            If true, HSE teams can intervene before incidents occur rather than 
            investigating after they happen. This page provides the statistical evidence.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        section_header("SCI vs LTI Probability — Scatter Plot")
        # Aggregate: for each SCI range, what % of weeks had LTI in next 30 days?
        snapshots["sci_bin"] = pd.cut(
            snapshots["safety_culture_index"],
            bins=[0,40,55,70,85,100],
            labels=["<40 Poor","40-55 Fair","55-70 Fair+","70-85 Good","85+ Excellent"]
        )
        sci_lti = snapshots.groupby("sci_bin", observed=True).agg(
            lti_rate=("lti_next_30_days","mean"),
            count=("lti_next_30_days","count")
        ).reset_index()
        sci_lti["lti_pct"] = sci_lti["lti_rate"] * 100

        colors_bins = [T["danger"],T["warning"],T["accent"],T["primary"],T["good"]]
        fig_scatter = go.Figure(go.Bar(
            x=sci_lti["sci_bin"].astype(str),
            y=sci_lti["lti_pct"],
            marker_color=colors_bins[:len(sci_lti)],
            text=[f"{v:.1f}%" for v in sci_lti["lti_pct"]],
            textposition="outside",
        ))
        apply_layout(fig_scatter, height=300)
        fig_scatter.update_layout(
            yaxis_title="% Weeks with LTI in Next 30 Days",
            xaxis_title="Safety Culture Index Range",
            showlegend=False,
            margin=dict(l=55,r=20,t=20,b=80),
        )
        st.plotly_chart(fig_scatter, use_container_width=True, key="p2_to_p5_chart_9")
        st.caption("Lower SCI = higher LTI probability. This validates SCI as a genuine predictive indicator.")

    with col_r:
        section_header("Near Miss Ratio vs LTI Rate")
        snapshots["nm_bin"] = pd.cut(
            snapshots["near_miss_rate"],
            bins=[0,1,2,3,5,99],
            labels=["<1.0","1.0-2.0","2.0-3.0","3.0-5.0",">5.0"]
        )
        nm_lti = snapshots.groupby("nm_bin", observed=True).agg(
            lti_rate=("lti_next_30_days","mean")
        ).reset_index()
        nm_lti["lti_pct"] = nm_lti["lti_rate"] * 100

        fig_nm = go.Figure(go.Bar(
            x=nm_lti["nm_bin"].astype(str),
            y=nm_lti["lti_pct"],
            marker_color=[T["danger"],T["warning"],T["accent"],T["primary"],T["good"]],
            text=[f"{v:.1f}%" for v in nm_lti["lti_pct"]],
            textposition="outside",
        ))
        apply_layout(fig_nm, height=300)
        fig_nm.update_layout(
            yaxis_title="% Weeks with LTI in Next 30 Days",
            xaxis_title="Near Miss Rate (per 100 workers)",
            showlegend=False,
            margin=dict(l=55,r=20,t=20,b=80),
        )
        st.plotly_chart(fig_nm, use_container_width=True, key="p2_to_p5_chart_10")
        st.caption("Higher near miss reporting correlates with LOWER LTI rates — confirming healthy reporting culture reduces harm.")

    # Training compliance vs LTI
    section_header("Training Compliance vs LTI Rate — Monthly Aggregated")
    monthly = get_monthly_sci()
    if not monthly.empty:
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Scatter(
            x=monthly["avg_training_compliance"],
            y=monthly["lti_count"],
            mode="markers",
            marker=dict(
                size=10,
                color=monthly["avg_sci"],
                colorscale=[[0,T["danger"]],[0.5,T["accent"]],[1,T["good"]]],
                colorbar=dict(title="SCI"),
                opacity=0.8,
            ),
            text=monthly["department"] + " " + monthly["year_month"],
            hovertemplate="%{text}<br>Training: %{x:.0f}%<br>LTI: %{y}",
        ))
        apply_layout(fig_tr, height=320)
        fig_tr.update_layout(
            xaxis_title="Training Compliance %",
            yaxis_title="LTI Count",
            showlegend=False,
            margin=dict(l=55,r=20,t=20,b=60),
        )
        st.plotly_chart(fig_tr, use_container_width=True, key="p2_to_p5_chart_11")
        st.caption("Each point = one department-month. Colour = SCI score. Departments with lower training compliance cluster toward higher LTI counts.")
