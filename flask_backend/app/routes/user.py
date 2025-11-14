from __future__ import annotations
from flask import Blueprint, request, jsonify, g
from .utils import require_fields
from ..middlewares.auth import require_auth
from ..controllers.user_controller import upsert_profile_controller
from app.services.supabase_service import get_supabase_service  # type: ignore

bp = Blueprint('user', __name__, url_prefix='/api/user')


@bp.post('/profile')
@require_auth
def upsert_profile():
    data = request.get_json(force=True)
    require_fields(data, ['age','weight_kg','height_cm','gender'])
    # user_id từ JWT (g.user_id)
    payload = {**data, 'user_id': g.user_id}
    res = upsert_profile_controller(payload)
    return jsonify(res)


@bp.get('/profile')
@require_auth
def get_profile():
    sb = get_supabase_service()
    prof = sb.get_profile(g.user_id)
    if not prof:
        return jsonify({"success": False, "error": "Profile not found"}), 404
    return jsonify({"success": True, "profile": prof})


@bp.delete('/account')
@require_auth
def delete_account():
    """Delete the current authenticated user from Supabase Auth.
    Requires server to be configured with service role key.
    """
    sb = get_supabase_service()
    try:
        # supabase-py v2 admin delete
        sb.client.auth.admin.delete_user(g.user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.post('/avatar')
@require_auth
def upload_avatar():
    """Upload avatar using service role (bypasses storage RLS) and upsert public.users.url_image.
    Accepts multipart/form-data with field 'file' and optional 'email'.
    """
    sb = get_supabase_service()
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400
    f = request.files['file']
    email = request.form.get('email')
    try:
        # Upload to storage via service account
        public_url = sb.upload_image(g.user_id, f.read(), f.filename)
        if not public_url:
            return jsonify({"success": False, "error": "Upload failed"}), 500
        # Ensure we have an email to satisfy NOT NULL on public.users.email
        if not email:
            try:
                # Try existing row
                res = sb.client.table('users').select('email').eq('user_id', g.user_id).limit(1).execute()
                data = getattr(res, 'data', None) or []
                if isinstance(data, list) and data:
                    email = data[0].get('email')
            except Exception:
                pass
        if not email:
            try:
                # Try admin API
                usr = sb.client.auth.admin.get_user_by_id(g.user_id)
                u = getattr(usr, 'user', None)
                if isinstance(u, dict):
                    email = u.get('email')
                else:
                    email = getattr(u, 'email', None)
            except Exception:
                pass
        # Upsert users row
        payload = {"user_id": g.user_id, "url_image": public_url}
        if email:
            payload["email"] = email
        sb.client.table('users').upsert(payload, on_conflict='user_id').execute()
        return jsonify({"success": True, "url": public_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
