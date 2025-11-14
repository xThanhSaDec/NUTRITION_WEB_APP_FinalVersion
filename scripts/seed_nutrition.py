from __future__ import annotations
import os
import csv
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
CSV_PATH = os.getenv("NUTRITION_CSV", os.path.join(os.path.dirname(__file__), "..", "data", "nutrition_database.csv"))

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    path = os.path.abspath(CSV_PATH)
    if not os.path.exists(path):
        raise SystemExit(f"CSV not found: {path}")
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            r2 = {k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            r2['dish_name'] = (r2.get('dish_name') or '').strip().lower()
            # Coerce numerics
            for k in ['calories','protein','fat','carbs','fiber']:
                try:
                    r2[k] = float(r2.get(k) or 0)
                except Exception:
                    r2[k] = 0.0
            rows.append(r2)
    # Upsert in chunks
    CHUNK = 500
    for i in range(0, len(rows), CHUNK):
        batch = rows[i:i+CHUNK]
        print(f"Upserting {i+1}-{i+len(batch)} / {len(rows)} ...")
        client.table('nutrition').upsert(batch, on_conflict='dish_name').execute()
    print("Done.")
