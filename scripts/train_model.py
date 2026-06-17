"""HSIP Platform — ML Model Training Script"""

import sys
from pathlib import Path

for _p in [str(Path(__file__).resolve().parent.parent), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def main():
    print("=" * 60)
    print("HSIP — LTI Prediction Model Training")
    print("=" * 60)

    from models.predictor import train_model, score_all_departments

    print("\n[Step 1] Training LTI prediction model...")
    metadata = train_model()
    print(f"  ✓ Model: {metadata['model_type']}")
    print(f"  ✓ ROC-AUC: {metadata['roc_auc']:.4f}")
    print(f"  ✓ Recall:  {metadata['recall']:.3f}")
    print(f"  ✓ F1:      {metadata['f1']:.3f}")

    print("\n[Step 2] Scoring all departments...")
    scores = score_all_departments()
    for _, row in scores.iterrows():
        print(f"  {row['department'][:35]:<35} "
              f"{row['lti_probability_30d']*100:.0f}% — {row['risk_level']}")

    print("\n" + "=" * 60)
    print("✅ HSIP Model Training Complete")
    print("   Run: streamlit run dashboards/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
