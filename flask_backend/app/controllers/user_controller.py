from __future__ import annotations
from typing import Dict, Any

from app.services.nutrition_goal_service import calculate_targets, Profile  # type: ignore
from app.services.supabase_service import get_supabase_service  # type: ignore


def upsert_profile_controller(payload: Dict[str, Any]) -> Dict[str, Any]:
    p = Profile(
        age=int(payload["age"]),
        weight_kg=float(payload["weight_kg"]),
        height_cm=float(payload["height_cm"]),
        gender=str(payload["gender"]).lower(),
        activity=str(payload.get("activity", "moderate")),
    )
    targets = calculate_targets(p)
    sb = get_supabase_service()
    fields: Dict[str, Any] = {
        "age": p.age,
        "weight_kg": p.weight_kg,
        "height_cm": p.height_cm,
        "gender": p.gender,
        "activity": p.activity,
        "targets": targets,
    }
    # Optional goal_weight if provided
    gw = payload.get("goal_weight")
    if gw is not None and gw != "":
        try:
            fields["goal_weight"] = float(gw)
        except Exception:
            pass
    saved = sb.upsert_profile(payload["user_id"], fields)
    return {"success": True, "profile": saved, "targets": targets}
