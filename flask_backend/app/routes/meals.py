from __future__ import annotations
from flask import Blueprint, request, jsonify, g
from ..middlewares.auth import require_auth
from .utils import require_fields
from ..controllers.meals_controller import (
    log_meal_controller,
    meals_today_controller,
)
from app.services.supabase_service import get_supabase_service  # type: ignore
from datetime import date, datetime, timedelta, timezone
from ..services.nutrition_goal_service import calculate_targets, Profile  # type: ignore

bp = Blueprint('meals', __name__, url_prefix='/api')


@bp.post('/meals/log')
@require_auth
def log_meal():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        try:
            servings = float(request.form.get('servings', 1))
        except Exception:
            return jsonify({"success": False, "error": "Invalid servings"}), 400
        meal_type = request.form.get('meal_type', 'unspecified')
        # Optional model selection to align with /api/predict
        model_key = request.form.get('model')
        f = request.files['file']
        res = log_meal_controller(g.user_id, meal_type, servings, f.filename, f.read(), model_key=model_key)
        status = 200 if res.get('success') else 500
        return jsonify(res), status
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected server error: {str(e)}"}), 500


@bp.get('/meals/today')
@require_auth
def meals_today():
    return jsonify(meals_today_controller(g.user_id))


@bp.get('/meals/history')
@require_auth
def meals_history():
    s = request.args.get('start')
    e = request.args.get('end')
    today = date.today()
    try:
        start_d = datetime.fromisoformat(s).date() if s else (today - timedelta(days=7))
    except Exception:
        start_d = today - timedelta(days=7)
    try:
        end_d = datetime.fromisoformat(e).date() if e else today
    except Exception:
        end_d = today
    # Ensure start <= end
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    # Compute local timezone day window and convert to UTC
    local_tz = datetime.now().astimezone().tzinfo
    start_local = datetime.combine(start_d, datetime.min.time(), tzinfo=local_tz)
    # inclusive end day -> add one day then use half-open [start, end)
    end_local_plus = datetime.combine(end_d + timedelta(days=1), datetime.min.time(), tzinfo=local_tz)
    start_utc = start_local.astimezone(timezone.utc).isoformat()
    end_utc = end_local_plus.astimezone(timezone.utc).isoformat()
    sb = get_supabase_service()
    res = (sb.client.table('food_logs').select('*')
           .eq('user_id', g.user_id)
           .gte('created_at', start_utc)
           .lt('created_at', end_utc)
           .order('created_at', desc=False).execute())
    logs = res.data or []
    daily = {}
    for r in logs:
        day = r['created_at'][:10]
        daily.setdefault(day, {"calories":0.0,"protein":0.0,"fat":0.0,"carbs":0.0,"fiber":0.0})
        for k in ["calories","protein","fat","carbs","fiber"]:
            daily[day][k] += float(r.get(k,0) or 0)
    return jsonify({"success": True, "range": {"start": start_d.isoformat(), "end": end_d.isoformat()}, "logs": logs, "daily_totals": daily})


@bp.get('/streak')
@require_auth
def streak():
    sb = get_supabase_service()
    start = (date.today() - timedelta(days=60)).isoformat()
    res = (sb.client.table('daily_summaries').select('day, complete')
           .eq('user_id', g.user_id).gte('day', start).order('day', desc=True).execute())
    st = 0
    for row in (res.data or []):
        if row.get('complete'): st += 1
        else: break
    return jsonify({"success": True, "streak": st})


@bp.delete('/meals/log/<log_id>')
@require_auth
def delete_meal_log(log_id: str):
    """Delete one meal log owned by the current user."""
    try:
        sb = get_supabase_service()
        res = (sb.client.table('food_logs')
               .delete()
               .eq('id', log_id)
               .eq('user_id', g.user_id)
               .execute())
        # Supabase returns deleted rows in res.data for some versions; success even if 0 rows
        return jsonify({"success": True, "deleted": len(getattr(res, 'data', []) or [])})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _parse_local_range(start_str: str | None, end_str: str | None):
    today = date.today()
    try:
        start_d = datetime.fromisoformat(start_str).date() if start_str else (today - timedelta(days=30))
    except Exception:
        start_d = today - timedelta(days=30)
    try:
        end_d = datetime.fromisoformat(end_str).date() if end_str else today
    except Exception:
        end_d = today
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    local_tz = datetime.now().astimezone().tzinfo
    start_local = datetime.combine(start_d, datetime.min.time(), tzinfo=local_tz)
    end_local_plus = datetime.combine(end_d + timedelta(days=1), datetime.min.time(), tzinfo=local_tz)
    start_utc = start_local.astimezone(timezone.utc).isoformat()
    end_utc = end_local_plus.astimezone(timezone.utc).isoformat()
    return start_d, end_d, start_utc, end_utc, local_tz


@bp.get('/stats/series')
@require_auth
def stats_series():
    """Return time-series of nutrition totals for the user between start..end.
    Query params:
      - start, end: YYYY-MM-DD (inclusive)
      - bucket: day|week|month|year (default: day)
      - goal_weight: optional float to adjust targets up/down from profile
    Response includes: series (array), labels, applied_targets, advice, recommendations
    """
    s = request.args.get('start')
    e = request.args.get('end')
    bucket = (request.args.get('bucket') or 'day').lower()
    if bucket not in ('day','week','month','year'):
        bucket = 'day'
    goal_weight = request.args.get('goal_weight')

    start_d, end_d, start_utc, end_utc, local_tz = _parse_local_range(s, e)
    sb = get_supabase_service()
    res = (sb.client.table('food_logs').select('*')
           .eq('user_id', g.user_id)
           .gte('created_at', start_utc)
           .lt('created_at', end_utc)
           .order('created_at', desc=False).execute())
    rows = res.data or []

    # Helper to parse created_at to local datetime
    def to_local_dt(ts):
        try:
            dt = datetime.fromisoformat(str(ts))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(local_tz)
        except Exception:
            return None

    # Bucket function
    def bucket_key_and_sort(dt: datetime):
        if bucket == 'day':
            key = dt.date().isoformat()
            sort_k = datetime(dt.year, dt.month, dt.day, tzinfo=local_tz)
        elif bucket == 'week':
            y, w, _ = dt.isocalendar()
            key = f"{y}-W{int(w):02d}"
            # Monday of ISO week
            monday = (dt - timedelta(days=dt.weekday())).date()
            sort_k = datetime(monday.year, monday.month, monday.day, tzinfo=local_tz)
        elif bucket == 'month':
            key = f"{dt.year}-{int(dt.month):02d}"
            sort_k = datetime(dt.year, dt.month, 1, tzinfo=local_tz)
        else:  # year
            key = f"{dt.year}"
            sort_k = datetime(dt.year, 1, 1, tzinfo=local_tz)
        return key, sort_k

    # Aggregate
    agg: dict[str, dict] = {}
    for r in rows:
        dt = to_local_dt(r.get('created_at'))
        if not dt:
            continue
        key, sort_k = bucket_key_and_sort(dt)
        a = agg.setdefault(key, {"calories":0.0,"protein":0.0,"fat":0.0,"carbs":0.0,"fiber":0.0, "_sort": sort_k })
        for k in ("calories","protein","fat","carbs","fiber"):
            a[k] += float(r.get(k,0) or 0)

    # Sort buckets by sort key
    items = sorted(agg.items(), key=lambda kv: kv[1]["_sort"]) if agg else []
    labels = [k for k,_ in items]
    series = [{"key": k, **{m:v for m,v in d.items() if m != "_sort"}} for k,d in items]

    # Compute targets from profile and optional goal_weight adjustment
    prof = sb.get_profile(g.user_id) or {}
    try:
        p = Profile(
            age=int(prof.get('age') or 25),
            weight_kg=float(prof.get('weight_kg') or 60.0),
            height_cm=float(prof.get('height_cm') or 170.0),
            gender=str(prof.get('gender') or 'male'),
            activity=str(prof.get('activity') or 'moderate')
        )
        base_targets = calculate_targets(p)
    except Exception:
        base_targets = {"calories":2000.0,"protein":100.0,"fat":70.0,"carbs":250.0,"fiber":25.0}

    applied = dict(base_targets)
    # Use profile.goal_weight when query param is not provided
    if not goal_weight:
        try:
            gwp = prof.get('goal_weight')
            if gwp is not None:
                goal_weight = str(gwp)
        except Exception:
            pass
    if goal_weight:
        try:
            gw = float(goal_weight)
            curw = float(prof.get('weight_kg') or 0)
            if gw > 0 and curw > 0 and abs(gw - curw) > 0.25:
                # Adjust calories by +/-300; recompute macros split 20/30/50
                delta = 300.0 if gw > curw else -300.0
                cals = max(1200.0, base_targets.get('calories', 2000.0) + delta)
                applied = {
                    'calories': round(cals, 1),
                    'protein': round(0.20 * cals / 4.0, 1),
                    'fat':     round(0.30 * cals / 9.0, 1),
                    'carbs':   round(0.50 * cals / 4.0, 1),
                    'fiber':   base_targets.get('fiber', 25.0),
                }
        except Exception:
            pass

    # Advice based on average per day over the date range
    total_days = max(1, (end_d - start_d).days + 1)
    sums = {"calories":0.0,"protein":0.0,"fat":0.0,"carbs":0.0,"fiber":0.0}
    for _, d in items:
        for k in sums:
            sums[k] += float(d.get(k,0) or 0)
    avgs = {k: (sums[k]/total_days) for k in sums}

    advice = {"missing": {}, "excess": {}}
    for k in sums:
        t = float(applied.get(k, 0) or 0)
        v = float(avgs.get(k, 0) or 0)
        if t <= 0:
            continue
        if v < 0.8 * t:
            advice["missing"][k] = round(t - v, 1)
        elif v > 1.2 * t:
            advice["excess"][k] = round(v - t, 1)

    # Recommendations for missing macros from nutrition dataset
    recs: dict[str, list] = {}
    try:
        for m in advice["missing"].keys():
            if m not in ("calories","protein","fat","carbs","fiber"):
                continue
            q = (sb.client.table('nutrition')
                 .select('dish_name, calories, protein, fat, carbs, fiber, serving')
                 .order(m, desc=True).limit(5).execute())
            recs[m] = q.data or []
    except Exception:
        recs = {}

    return jsonify({
        "success": True,
        "labels": labels,
        "series": series,
        "applied_targets": applied,
        "advice": advice,
        "recommendations": recs,
        "range": {"start": start_d.isoformat(), "end": end_d.isoformat()},
        "bucket": bucket,
    })
