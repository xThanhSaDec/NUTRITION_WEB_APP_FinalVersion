from __future__ import annotations
import os
from typing import Dict, Any, Optional

import pandas as pd

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
            csv_path = None
            for p in CANDIDATE_CSV:
                if os.path.exists(p):
                    csv_path = p
                    break
            if not csv_path:
                raise FileNotFoundError("nutrition_database.csv not found in data/")
            self.df = pd.read_csv(csv_path)
            # normalize
            self.df['dish_name_norm'] = self.df['dish_name'].astype(str).str.strip().str.lower()
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
        row = self.df[self.df['dish_name_norm'] == key].head(1)
        if row.empty:
            return {"success": False, "error": f"Nutrition not found for {class_name}"}
        r = row.iloc[0]
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
