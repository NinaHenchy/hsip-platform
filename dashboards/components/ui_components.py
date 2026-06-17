"""
HSIP Platform — UI Components
Distinctive Teal/Emerald Theme — visually different from ORPMI and HSEI
"""

import streamlit as st
import plotly.graph_objects as go

# Teal colour palette
T = {
    "primary":   "#0d7377",
    "secondary": "#14a085",
    "accent":    "#f0a500",
    "danger":    "#c0392b",
    "warning":   "#e67e22",
    "good":      "#1a8a5a",
    "bg":        "#f0f7f7",
    "card":      "#ffffff",
    "card_teal": "#e8f5f5",
    "border":    "#b8d8d8",
    "border_dark":"#7fb3b3",
    "text":      "#0d2b2b",
    "text_sub":  "#2d5a5a",
    "text_muted":"#4a8080",
    "grid":      "#daeaea",
    "plotly_bg": "#ffffff",
    "plotly_paper": "#f0f7f7",
}

RISK_COLORS = {
    "Critical": "#c0392b",
    "High":     "#e67e22",
    "Medium":   "#f0a500",
    "Low":      "#1a8a5a",
}

SCI_COLORS = {
    "excellent": "#1a8a5a",
    "good":      "#0d7377",
    "fair":      "#f0a500",
    "poor":      "#c0392b",
}

DEPT_COLORS = [
    "#0d7377","#14a085","#1a8a5a","#f0a500","#e67e22",
    "#c0392b","#8e44ad","#2980b9","#16a085","#d35400","#7f8c8d"
]

GLOBAL_CSS = f"""
<style>
/* ── Page background ── */
.stApp {{
    background-color: {T['bg']};
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background: linear-gradient(135deg, {T['card']} 0%, {T['card_teal']} 100%);
    border: 1px solid {T['border']};
    border-left: 4px solid {T['primary']};
    border-radius: 10px;
    padding: 14px 18px;
}}
[data-testid="stMetric"] label {{
    color: {T['text_sub']} !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}}
[data-testid="stMetricValue"] {{
    color: {T['text']} !important;
    font-size: 26px !important;
    font-weight: 800 !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0d2b2b 0%, #0d3d3d 100%);
}}
[data-testid="stSidebar"] * {{
    color: #c8e8e8 !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    color: #c8e8e8 !important;
    font-size: 13px !important;
}}

/* ── Cards ── */
.hsip-card {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 10px;
}}
.hsip-card-teal {{
    background: linear-gradient(135deg, {T['card_teal']} 0%, #ffffff 100%);
    border: 1px solid {T['border_dark']};
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 10px;
}}
.section-header {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: {T['primary']};
    border-bottom: 2px solid {T['primary']};
    padding-bottom: 7px;
    margin-bottom: 16px;
    font-weight: 700;
}}
.badge-critical {{ background:#fdecea;color:#c0392b;border:1px solid #f5b7b1;border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700; }}
.badge-high     {{ background:#fef3e2;color:#e67e22;border:1px solid #f9c97a;border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700; }}
.badge-medium   {{ background:#fefae2;color:#b8860b;border:1px solid #f0d060;border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700; }}
.badge-low      {{ background:#e2f5ee;color:#1a8a5a;border:1px solid #7dd3ab;border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700; }}
.alert-critical {{ background:#fdecea;border:1px solid #c0392b;border-left:5px solid #c0392b;border-radius:8px;padding:14px 18px;margin:10px 0;color:#c0392b; }}
.alert-warning  {{ background:#fef3e2;border:1px solid #e67e22;border-left:5px solid #e67e22;border-radius:8px;padding:14px 18px;margin:10px 0;color:#c05000; }}
.alert-ok       {{ background:#e2f5ee;border:1px solid #1a8a5a;border-left:5px solid #1a8a5a;border-radius:8px;padding:14px 18px;margin:10px 0;color:#1a8a5a; }}
hr {{ border-color: {T['border']}; margin: 20px 0; }}
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:22px;border-bottom:3px solid {T['primary']};padding-bottom:14px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:26px;">{icon}</span>
            <h1 style="color:{T['text']};font-size:22px;font-weight:800;margin:0;">{title}</h1>
        </div>
        {"<p style='color:"+T['text_sub']+";font-size:13px;margin:6px 0 0 38px;'>"+subtitle+"</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def section_header(text: str):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def alert_banner(message: str, level: str = "critical"):
    icons = {"critical": "🔴", "warning": "🟠", "ok": "🟢"}
    st.markdown(f'<div class="alert-{level}">{icons.get(level,"")} {message}</div>',
                unsafe_allow_html=True)


def sci_gauge_color(sci: float) -> str:
    if sci >= 85: return T["good"]
    elif sci >= 70: return T["primary"]
    elif sci >= 55: return T["accent"]
    return T["danger"]


def apply_layout(fig: go.Figure, title: str = "", height: int = 340) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color=T["text_sub"], size=12), x=0),
        paper_bgcolor=T["plotly_paper"],
        plot_bgcolor=T["plotly_bg"],
        font=dict(color=T["text"], size=12),
        height=height,
        margin=dict(l=50, r=20, t=40 if title else 20, b=50),
        xaxis=dict(gridcolor=T["grid"], linecolor=T["border"],
                   tickfont=dict(size=11, color=T["text_sub"]), zeroline=False),
        yaxis=dict(gridcolor=T["grid"], linecolor=T["border"],
                   tickfont=dict(size=11, color=T["text_sub"]), zeroline=False),
        hoverlabel=dict(bgcolor=T["card"], bordercolor=T["border"],
                        font=dict(size=12, color=T["text"])),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor=T["border"],
                    borderwidth=1, font=dict(size=11)),
    )
    return fig
