#!/bin/bash
set -e
cd /app
export PYTHONPATH=/app

echo "============================================================"
echo "HSIP Platform Starting..."
echo "============================================================"

if [ ! -f "database/hsip_dev.db" ]; then
    echo "Step 1/2: Initialising database..."
    python scripts/setup_database.py
    echo "Database ready."
fi

if [ ! -f "models/artifacts/hsip_model.pkl" ]; then
    echo "Step 2/2: Training prediction model..."
    python scripts/train_model.py
    echo "Model ready."
fi

echo "Launching Streamlit on port 8501..."
exec streamlit run dashboards/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false