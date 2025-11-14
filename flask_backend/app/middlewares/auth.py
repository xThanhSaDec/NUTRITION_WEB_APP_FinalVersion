from __future__ import annotations

import os
from functools import wraps
from typing import Callable, Optional, Any, Dict
from flask import request, jsonify, g

from dotenv import load_dotenv
load_dotenv()

# Use local services package directly
from app.services.supabase_service import get_supabase_service  # type: ignore

REQUIRE_JWT = os.getenv("REQUIRE_JWT", "true").lower() == "true"
DEMO_USER_ID = os.getenv("DEMO_USER_ID", "").strip()


def _extract_user_id(user_obj: Any) -> Optional[str]:
    # supabase-py may return a dict or object with attributes
    if not user_obj:
        return None
    if isinstance(user_obj, dict):
        return user_obj.get('id') or user_obj.get('user_id')
    return getattr(user_obj, 'id', None)


def require_auth(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Allow disabled mode (for local dev)
        if not REQUIRE_JWT:
            # Dev mode: if a Bearer token is provided, validate it and proceed like normal
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1].strip()
                try:
                    sb = get_supabase_service()
                    res = sb.client.auth.get_user(token)
                    user = getattr(res, "user", None)
                    uid = _extract_user_id(user)
                    if not uid:
                        return jsonify({"success": False, "error": "Invalid token"}), 401
                    g.user_id = uid
                    try:
                        email = None
                        display_name = None
                        url_image = None
                        if isinstance(user, dict):
                            email = user.get('email')
                            meta = user.get('user_metadata') or {}
                            if isinstance(meta, dict):
                                display_name = meta.get('display_name') or meta.get('full_name')
                                url_image = meta.get('avatar_url') or meta.get('picture')
                        else:
                            email = getattr(user, 'email', None)
                            meta = getattr(user, 'user_metadata', None) or {}
                            if isinstance(meta, dict):
                                display_name = meta.get('display_name') or meta.get('full_name')
                                url_image = meta.get('avatar_url') or meta.get('picture')
                        sb.upsert_user(uid, email=email, display_name=display_name, url_image=url_image)
                    except Exception:
                        pass
                    return fn(*args, **kwargs)
                except Exception:
                    # Fall through to header/env fallback below
                    pass
            # Otherwise, require X-User-Id header or DEMO_USER_ID env var
            uid = request.headers.get('X-User-Id') or DEMO_USER_ID
            if not uid:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized (dev): Provide X-User-Id header with a valid Supabase auth user id, or set DEMO_USER_ID in .env, or enable REQUIRE_JWT=true and login."
                }), 401
            g.user_id = uid
            return fn(*args, **kwargs)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"success": False, "error": "Missing Bearer token"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            sb = get_supabase_service()
            # Validate token using admin api
            res = sb.client.auth.get_user(token)
            user = getattr(res, "user", None)
            uid = _extract_user_id(user)
            if not uid:
                return jsonify({"success": False, "error": "Invalid token"}), 401
            # Stash user id for downstream handlers
            g.user_id = uid
            # Best-effort upsert into public.users for app bookkeeping
            try:
                email = None
                display_name = None
                url_image = None
                if isinstance(user, dict):
                    email = user.get('email')
                    meta = user.get('user_metadata') or {}
                    if isinstance(meta, dict):
                        display_name = meta.get('display_name') or meta.get('full_name')
                        url_image = meta.get('avatar_url') or meta.get('picture')
                else:
                    email = getattr(user, 'email', None)
                    meta = getattr(user, 'user_metadata', None) or {}
                    if isinstance(meta, dict):
                        display_name = meta.get('display_name') or meta.get('full_name')
                        url_image = meta.get('avatar_url') or meta.get('picture')
                sb.upsert_user(uid, email=email, display_name=display_name, url_image=url_image)
            except Exception:
                pass
        except Exception:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper
