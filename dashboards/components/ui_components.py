"""HSIP Dashboard — Deep Teal Slate Industrial Theme"""
import streamlit as st
import plotly.graph_objects as go

THEME = {
    "bg_primary":     "#0a1a1f",
    "bg_secondary":   "#0f2228",
    "bg_card":        "#0f2228",
    "bg_elevated":    "#162d35",
    "border":         "#1e3d47",
    "border_light":   "#2a4d5a",
    "text_primary":   "#e8f4f8",
    "text_secondary": "#7aaab8",
    "text_muted":     "#3d6070",
    "green":   "#06d6a0",
    "amber":   "#f59e0b",
    "red":     "#ef4444",
    "orange":  "#f97316",
    "blue":    "#00b4d8",
    "cyan":    "#48cae4",
    "purple":  "#818cf8",
    "teal":    "#00b4d8",
    "mint":    "#06d6a0",
    "plotly_bg":    "#0f2228",
    "plotly_paper": "#0a1a1f",
    "grid_color":   "#1e3d47",
    "axis_color":   "#3d6070",
}

RISK_COLORS = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#f59e0b",
    "Low":      "#06d6a0",
}

SEVERITY_COLORS = RISK_COLORS.copy()

GLOBAL_CSS = """
<style>
.stApp{background-color:#0a1a1f}
[data-testid="stSidebar"]{background-color:#061015!important;border-right:1px solid #1e3d47}
[data-testid="stSidebar"] *{color:#7aaab8!important}
[data-testid="stSidebar"] .stRadio label{color:#a8ccd8!important;font-size:13px!important}
[data-testid="stSidebar"] .stRadio label:hover{color:#00b4d8!important}
[data-testid="stMetric"]{background:linear-gradient(135deg,#0f2228,#162d35);border:1px solid #1e3d47;border-left:3px solid #00b4d8;border-radius:8px;padding:14px 18px}
[data-testid="stMetric"] label{color:#7aaab8!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.08em}
[data-testid="stMetricValue"]{color:#e8f4f8!important;font-size:24px!important;font-weight:700!important}
.stTabs [data-baseweb="tab"]{background-color:#0f2228;border:1px solid #1e3d47;color:#7aaab8;border-radius:6px 6px 0 0}
.stTabs [aria-selected="true"]{background-color:#162d35!important;color:#00b4d8!important;border-bottom:2px solid #00b4d8!important}
[data-testid="stForm"]{background-color:#0f2228;border:1px solid #1e3d47;border-radius:10px;padding:20px}
.stButton>button{background:linear-gradient(135deg,#00b4d8,#0891b2);color:#0a1a1f;border:none;font-weight:700;border-radius:6px}
.stButton>button:hover{background:linear-gradient(135deg,#0096c7,#0773a0);color:#fff}
hr{border-color:#1e3d47}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:#0a1a1f}
::-webkit-scrollbar-thumb{background:#1e3d47;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#00b4d8}
</style>
"""

def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f2228,#162d35);border:1px solid #1e3d47;
                border-left:4px solid #00b4d8;border-radius:10px;padding:18px 24px;margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:28px;">{icon}</span>
            <div>
                <h1 style="color:#e8f4f8;font-size:22px;font-weight:800;margin:0;">{title}</h1>
                {"<p style='color:#7aaab8;font-size:13px;margin:4px 0 0;'>"+subtitle+"</p>" if subtitle else ""}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

def section_header(text: str):
    st.markdown(f"""
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:#00b4d8;
                border-bottom:1px solid #1e3d47;padding-bottom:8px;margin-bottom:16px;
                margin-top:8px;font-weight:700;">{text}</div>""", unsafe_allow_html=True)

def alert_banner(message: str, level: str = "critical"):
    colors = {
        "critical": ("#ef4444", "#1a0808"),
        "warning":  ("#f59e0b", "#1a1400"),
        "info":     ("#00b4d8", "#081520"),
        "success":  ("#06d6a0", "#081a18"),
    }
    color, bg = colors.get(level, colors["info"])
    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵", "success": "🟢"}
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {color};border-left:4px solid {color};
                border-radius:8px;padding:12px 18px;margin:8px 0;color:{color};
                font-size:13px;font-weight:600;">{icons.get(level,"")} {message}</div>
    """, unsafe_allow_html=True)

def apply_layout(fig: go.Figure, title: str = "", height: int = 340) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color="#7aaab8", size=12), x=0),
        paper_bgcolor="#0a1a1f",
        plot_bgcolor="#0f2228",
        font=dict(color="#e8f4f8", size=12),
        height=height,
        margin=dict(l=50, r=20, t=40 if title else 20, b=50),
        xaxis=dict(gridcolor="#1e3d47", linecolor="#1e3d47",
                   tickfont=dict(size=11, color="#3d6070"), zeroline=False),
        yaxis=dict(gridcolor="#1e3d47", linecolor="#1e3d47",
                   tickfont=dict(size=11, color="#3d6070"), zeroline=False),
        hoverlabel=dict(bgcolor="#162d35", bordercolor="#1e3d47",
                        font=dict(size=12, color="#e8f4f8")),
        legend=dict(bgcolor="rgba(15,34,40,0.9)", bordercolor="#1e3d47",
                    borderwidth=1, font=dict(size=11, color="#e8f4f8")),
    )
    return fig


# ── Convenience alias ─────────────────────────────────────────────────────
T = THEME


# ── SCI colour helper ─────────────────────────────────────────────────────
def sci_gauge_color(sci: float) -> str:
    if sci >= 80:   return THEME["green"]
    if sci >= 65:   return THEME["blue"]
    if sci >= 50:   return THEME["amber"]
    return THEME["red"]


# ── Department colour palette ─────────────────────────────────────────────
DEPT_COLORS = {
    "Operations":           "#00b4d8",
    "Maintenance":          "#06d6a0",
    "HSE":                  "#f59e0b",
    "Drilling":             "#ef4444",
    "Process Engineering":  "#818cf8",
    "Logistics":            "#48cae4",
    "Contractor":           "#f97316",
    "Management":           "#7aaab8",
    "Electrical":           "#a78bfa",
    "Instrumentation":      "#34d399",
    "Quality Assurance":    "#fbbf24",
}


# ── SCI threshold colour map ─────────────────────────────────────────────
SCI_COLORS = {
    "Excellent": "#06d6a0",
    "Good":      "#00b4d8",
    "Fair":      "#f59e0b",
    "Poor":      "#ef4444",
}


# ── Legacy key aliases — required by page files ───────────────────────────
THEME["primary"]    = "#00b4d8"
THEME["secondary"]  = "#06d6a0"
THEME["accent"]     = "#00b4d8"
THEME["card"]       = "#0f2228"
THEME["card_teal"]  = "#162d35"
THEME["text"]       = "#e8f4f8"
THEME["text_sub"]   = "#7aaab8"
THEME["grid"]       = "#1e3d47"
THEME["good"]       = "#06d6a0"
THEME["warning"]    = "#f59e0b"
THEME["danger"]     = "#ef4444"