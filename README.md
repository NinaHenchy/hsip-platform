# HSIP Platform
### HSE Incident Prediction & Safety Culture Intelligence

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-teal)](https://hsip-platform-ninahenchy.streamlit.app/)

> The only platform in the portfolio that is **purely predictive on safety data**.
> Predicts Lost Time Injuries 30 days ahead from leading safety indicators.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)](https://streamlit.io)
[![Model](https://img.shields.io/badge/Model-Gradient%20Boosting-teal)](.)
[![Tests](https://img.shields.io/badge/Tests-19%20Passed-brightgreen)](.)
[![Standard](https://img.shields.io/badge/Standard-ISO%2045001-orange)](.)

![Dashboard](docs/screenshots/dashboard_preview.png)

---

## What Makes This Platform Unique

| Feature | Detail |
|---|---|
| **Prediction target** | 30-day LTI probability per department |
| **ML approach** | Gradient Boosting + Isotonic Calibration |
| **Input data** | 5 leading indicators → Safety Culture Index |
| **Validation** | Temporal split (no data leakage) |
| **Visual theme** | Teal/Emerald — distinct identity |
| **Departments** | 11 operational departments, 285 workers |
| **Data** | 2 years × 11 depts = 2,288 weekly records |

---

## Safety Culture Index (SCI)

The SCI is a composite score (0–100) computed weekly per department:

| Component | Weight | What it measures |
|---|---|---|
| Near Miss Reporting Rate | 25% | Willingness to report — higher = healthier culture |
| Training Compliance | 25% | Competency of workforce |
| Inspection Score | 20% | Physical workplace conditions |
| Action Close-Out Rate | 20% | Follow-through on corrective actions |
| PTW Compliance | 10% | Permit to Work discipline |

---

## Dashboard Pages

| Page | Content |
|---|---|
| 🎯 Command Centre | SCI gauges all 11 departments, facility overview, alerts |
| 🔮 LTI Prediction | 30-day LTI probability per dept, feature importance, risk register |
| 📡 Leading Indicators | Near miss rate, training, PTW, radar charts |
| 🔍 Department Intelligence | Per-dept drill-down with SCI history and LTI correlation |
| 📊 Correlation Analysis | Statistical evidence: does SCI actually predict LTIs? |
| ➕ Data Entry | Log observations, update weekly performance, SCI calculator |

---

## Quick Start

```bash
git clone https://github.com/NinaHenchy/hsip-platform.git
cd hsip-platform
pip install -r requirements.txt
python scripts/setup_database.py
python scripts/train_model.py
streamlit run dashboards/app.py
```

## Docker

```bash
docker-compose up -d
# http://localhost:8504
```

---

## Portfolio Context

```
OPC-Alpha Facility Analytics Portfolio
├── ORPMI  ← Equipment reliability & predictive maintenance
├── HSEI   ← HSE incident analytics & process safety
└── HSIP   ← Safety culture intelligence & LTI prediction (this repo)
```

*Three platforms. One facility. Complete operational intelligence.*
