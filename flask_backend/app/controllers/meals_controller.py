from __future__ import annotations
from datetime import date, datetime
from typing import Dict, Any, List

from app.services.inference_service import get_inference_service  # type: ignore
from app.services.nutrition_service import get_nutrition_service  # type: ignore
from app.services.nutrition_goal_service import evaluate_day  # type: ignore
from app.services.supabase_service import get_supabase_service  # type: ignore


def log_meal_controller(user_id: str, meal_type: str, servings: float, filename: str, content: bytes) -> Dict[str, Any]:
    infer = get_inference_service()
    nutri = get_nutrition_service()
    sb = get_supabase_service()

    pred = infer.predict(content)
    if not pred.get("success"):
        return {"success": False, "error": pred.get("error", "predict failed")}

    nres = nutri.get_nutrition(pred.get("class_name", ""))
    nutrition = nres.get("nutrition") if nres.get("success") else {"calories":0,"protein":0,"fat":0,"carbs":0,"fiber":0}
    scaled = {k: float(v) * float(servings) for k, v in nutrition.items()}

    # Try to upload image; on failure, continue without image but include warning
    public_url = None
    try:
        public_url = sb.upload_image(user_id, content, filename)
    except Exception as e:
        # Proceed without image URL; caller can still save the meal, but surface reason
        public_url = None
        upload_error = str(e)

    log = {
        "user_id": user_id,
        "meal_type": meal_type,
        "image_url": public_url,
        "food_name": pred.get("food_name"),
        "class_name": pred.get("class_name"),
        "confidence": pred.get("confidence"),
        "servings": servings,
        **scaled,
    }
    try:
        saved = sb.insert_food_log(log)
        # Ensure at least the keys we attempted to write are returned
        if not saved:
            return {"success": False, "error": "Insert failed without details."}
        resp = {"success": True, "log": saved}
        if public_url is None:
            # Include error message if available
            resp["warning"] = "Image upload failed; saved without image." + (f" Reason: {upload_error}" if 'upload_error' in locals() else "")
        return resp
    except Exception as e:
        return {"success": False, "error": f"Database insert failed: {str(e)}"}


def meals_today_controller(user_id: str) -> Dict[str, Any]:
    sb = get_supabase_service()
    logs = sb.get_food_logs_by_day(user_id, date.today())
    totals = {"calories":0.0,"protein":0.0,"fat":0.0,"carbs":0.0,"fiber":0.0}
    for r in logs:
        for k in totals:
            totals[k] += float(r.get(k,0) or 0)
    prof = sb.get_profile(user_id) or {}
    targets = prof.get("targets") or {}
    evaluation = evaluate_day(totals, targets) if targets else {"complete": False, "missing": {}, "breakdown": {}}
    sb.upsert_daily_summary({"user_id": user_id, "day": date.today().isoformat(), "totals": totals, "complete": evaluation.get("complete", False)})
    return {"success": True, "date": date.today().isoformat(), "logs": logs, "totals": totals, "evaluation": evaluation}
