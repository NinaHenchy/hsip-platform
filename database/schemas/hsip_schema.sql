-- =============================================================================
-- HSIP Platform — Database Schema
-- HSE Incident Prediction & Safety Culture Intelligence
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TABLE: weekly_dept_snapshot
-- Core table: weekly safety performance per department.
-- This is the ML feature table — one row per dept per week.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weekly_dept_snapshot (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start_date             DATE    NOT NULL,
    week_number                 INTEGER NOT NULL,
    year                        INTEGER NOT NULL,
    department                  VARCHAR(80) NOT NULL,
    workforce_size              INTEGER,

    -- Leading Indicators (features for ML)
    near_miss_count             INTEGER DEFAULT 0,
    near_miss_rate              REAL,       -- per 100 workers per week
    unsafe_act_count            INTEGER DEFAULT 0,
    unsafe_condition_count      INTEGER DEFAULT 0,
    observation_count           INTEGER DEFAULT 0,
    swa_used                    INTEGER DEFAULT 0,  -- Stop Work Authority events

    inspection_score            REAL,       -- 0-100
    inspection_count            INTEGER DEFAULT 0,
    critical_findings           INTEGER DEFAULT 0,
    action_closeout_rate        REAL,       -- % actions closed on time
    overdue_actions             INTEGER DEFAULT 0,

    training_compliance_pct     REAL,       -- % with valid mandatory certs
    expired_certs               INTEGER DEFAULT 0,
    training_hours              REAL DEFAULT 0,

    ptw_issued                  INTEGER DEFAULT 0,
    ptw_violations              INTEGER DEFAULT 0,
    ptw_compliance_rate         REAL,       -- % permits with no violation

    toolbox_talks               INTEGER DEFAULT 0,
    management_walks            INTEGER DEFAULT 0,

    -- Safety Culture Index (computed)
    safety_culture_index        REAL,       -- 0-100 composite

    -- Lagging Indicators
    first_aid_count             INTEGER DEFAULT 0,
    medical_treatment_count     INTEGER DEFAULT 0,
    restricted_work_count       INTEGER DEFAULT 0,
    lti_count                   INTEGER DEFAULT 0,
    fatality_count              INTEGER DEFAULT 0,
    days_lost                   INTEGER DEFAULT 0,
    manhours                    REAL,

    -- ML Target
    lti_next_30_days            INTEGER DEFAULT 0,  -- Binary: LTI in next 30 days?

    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_start_date, department)
);

-- -----------------------------------------------------------------------------
-- TABLE: lti_events
-- Historical LTI and serious injury events by department.
-- Used to generate the prediction target variable.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lti_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date          DATE    NOT NULL,
    department          VARCHAR(80) NOT NULL,
    event_type          VARCHAR(60) NOT NULL,
    severity            VARCHAR(20),
    days_lost           INTEGER DEFAULT 0,
    description         TEXT,
    root_cause_category VARCHAR(100),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- TABLE: model_predictions
-- Stores ML model output: 30-day LTI probability per dept per week.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_predictions (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date         DATE    NOT NULL,
    department              VARCHAR(80) NOT NULL,
    lti_probability_30d     REAL,       -- 0.0 to 1.0
    risk_level              VARCHAR(20),-- Critical / High / Medium / Low
    sci_score               REAL,
    top_risk_factor         VARCHAR(100),
    recommendation          TEXT,
    model_version           VARCHAR(20),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prediction_date, department)
);

-- -----------------------------------------------------------------------------
-- TABLE: safety_observations_live
-- Data entry: live safety observations entered by users.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS safety_observations_live (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_date    DATE    NOT NULL,
    department          VARCHAR(80),
    observation_type    VARCHAR(60),
    description         TEXT    NOT NULL,
    potential_severity  VARCHAR(20),
    reported_by         VARCHAR(60),
    is_anonymous        INTEGER DEFAULT 0,
    immediate_action    TEXT,
    followup_required   INTEGER DEFAULT 0,
    followup_complete   INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- TABLE: monthly_sci_summary
-- Pre-aggregated monthly Safety Culture Index by department.
-- Feeds the culture trend dashboard.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monthly_sci_summary (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month              VARCHAR(7)  NOT NULL,
    department              VARCHAR(80) NOT NULL,
    avg_sci                 REAL,
    avg_near_miss_rate      REAL,
    avg_training_compliance REAL,
    avg_inspection_score    REAL,
    avg_action_closeout     REAL,
    avg_ptw_compliance      REAL,
    lti_count               INTEGER DEFAULT 0,
    near_miss_count         INTEGER DEFAULT 0,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year_month, department)
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_snap_date  ON weekly_dept_snapshot(week_start_date);
CREATE INDEX IF NOT EXISTS idx_snap_dept  ON weekly_dept_snapshot(department);
CREATE INDEX IF NOT EXISTS idx_lti_date   ON lti_events(event_date);
CREATE INDEX IF NOT EXISTS idx_pred_date  ON model_predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_sci_month  ON monthly_sci_summary(year_month);
