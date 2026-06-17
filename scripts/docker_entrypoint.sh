#!/bin/bash
set -e
echo "HSIP Platform starting..."
cd /app
export PYTHONPATH=/app

if [ ! -f "database/hsip_dev.db" ]; then
    echo "Initialising database..."
    python scripts/setup_database.py
fi

if [ ! -f "models/artifacts/hsip_model.pkl" ]; then
    echo "Training prediction model..."
    python scripts/train_model.py
fi

echo "Launching Streamlit..."
exec streamlit run dashboards/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
