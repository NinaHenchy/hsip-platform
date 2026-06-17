"""HSIP Platform — Setup Script"""

import sys
from pathlib import Path

for _p in [str(Path(__file__).resolve().parent.parent), "/app"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    print("=" * 60)
    print("HSIP Platform — Initial Setup")
    print("=" * 60)

    for d in ["data/raw","data/processed","database","logs","models/artifacts"]:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")

    print("\nInitialising database...")
    from database.db_connection import initialize_database, test_connection
    initialize_database()
    test_connection()
    print("  ✓ Schema created")

    print("\nRunning ETL pipeline...")
    from etl.extractors.synthetic_data_generator import run_full_generation
    from etl.loaders.db_loader import load_all_tables, verify_load
    from database.db_connection import get_engine

    data   = run_full_generation()
    engine = get_engine()
    load_all_tables(data, engine)
    verify_load(engine)

    print("\n" + "=" * 60)
    print("✅ HSIP Database ready.")
    print("   Run: python scripts/train_model.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
