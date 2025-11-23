from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Profile:
    age: int
    weight_kg: float
    height_cm: float
    gender: str  # 'male' | 'female'
    activity: str = 'moderate'


# Simple Mifflin-St Jeor + activity multiplier
_ACTIVITY = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}


def calculate_targets(p: Profile) -> Dict[str, float]:
    if p.gender.lower() == 'male':
        bmr = 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age + 5
    else:
        bmr = 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age - 161
    mult = _ACTIVITY.get(p.activity, 1.55)
    tdee = bmr * mult
    # Macro split: 20% protein, 30% fat, 50% carbs (by calories)
    protein_g = (0.20 * tdee) / 4.0
    fat_g = (0.30 * tdee) / 9.0
    carbs_g = (0.50 * tdee) / 4.0
    fiber_g = 25.0  # generic target
    return {
        'calories': float(round(tdee, 1)),
        'protein': float(round(protein_g, 1)),
        'fat': float(round(fat_g, 1)),
        'carbs': float(round(carbs_g, 1)),
        'fiber': float(round(fiber_g, 1)),
    }


def evaluate_day(totals: Dict[str, float], targets: Dict[str, float]) -> Dict[str, Any]:
    missing: Dict[str, float] = {}
    breakdown: Dict[str, float] = {}
    ok = True
    for k in ['calories', 'protein', 'fat', 'carbs', 'fiber']:
        t = float(targets.get(k, 0) or 0)
        v = float(totals.get(k, 0) or 0)
        breakdown[k] = v / t if t > 0 else 0.0
        if t > 0 and v + 1e-6 < 0.9 * t:  # allow 10% tolerance
            ok = False
            missing[k] = round(max(0.0, t - v), 1)
    return {'complete': ok, 'missing': missing, 'breakdown': breakdown}
