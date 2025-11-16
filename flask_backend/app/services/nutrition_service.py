from __future__ import annotations
import os, csv
from typing import Dict, Any, Optional

from .supabase_service import get_supabase_service

THIS_DIR = os.path.dirname(__file__)
CANDIDATE_CSV = [
    os.path.abspath(os.path.join(THIS_DIR, "..", "..", "..", "data", "nutrition_database.csv")),
    os.path.abspath(os.path.join(THIS_DIR, "..", "data", "nutrition_database.csv")),
]


class NutritionService:
    def __init__(self) -> None:
        self.use_supabase = os.getenv("USE_SUPABASE_NUTRITION", "false").lower() == "true"
        if not self.use_supabase:
            csv_path = next((p for p in CANDIDATE_CSV if os.path.exists(p)), None)
            if not csv_path:
                raise FileNotFoundError("nutrition_database.csv not found in data/")
            # Load CSV lightly (avoid pandas). Build list of dicts with normalized key.
            self._rows = []
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dish = (row.get('dish_name') or '').strip()
                    row['dish_name_norm'] = dish.lower()
                    # Convert numeric fields defensively
                    for k in ['calories','protein','fat','carbs','fiber']:
                        v = row.get(k)
                        try:
                            row[k] = float(v) if v not in (None, '') else 0.0
                        except Exception:
                            row[k] = 0.0
                    self._rows.append(row)
        else:
            # Ensure Supabase client is available
            self.sb = get_supabase_service()

    def get_nutrition(self, class_name: str) -> Dict[str, Any]:
        key = (class_name or '').strip().lower()
        if self.use_supabase:
            res = (self.sb.client.table('nutrition')
                   .select('*').eq('dish_name', key).maybe_single().execute())
            r = res.data
            if not r:
                return {"success": False, "error": f"Nutrition not found for {class_name}"}
            return {
                "success": True,
                "nutrition": {
                    "calories": float(r.get('calories', 0) or 0),
                    "protein": float(r.get('protein', 0) or 0),
                    "fat": float(r.get('fat', 0) or 0),
                    "carbs": float(r.get('carbs', 0) or 0),
                    "fiber": float(r.get('fiber', 0) or 0),
                },
                "serving": r.get('serving', None),
                "source": r.get('dataset_source', None),
            }
        # CSV fallback
        match = next((r for r in self._rows if r.get('dish_name_norm') == key), None)
        if not match:
            return {"success": False, "error": f"Nutrition not found for {class_name}"}
        r = match
        return {
            "success": True,
            "nutrition": {
                "calories": float(r.get('calories', 0) or 0),
                "protein": float(r.get('protein', 0) or 0),
                "fat": float(r.get('fat', 0) or 0),
                "carbs": float(r.get('carbs', 0) or 0),
                "fiber": float(r.get('fiber', 0) or 0),
            },
            "serving": r.get('serving', None),
            "source": r.get('dataset_source', None),
        }


_singleton: Optional[NutritionService] = None

def get_nutrition_service() -> NutritionService:
    global _singleton
    if _singleton is None:
        _singleton = NutritionService()
    return _singleton
