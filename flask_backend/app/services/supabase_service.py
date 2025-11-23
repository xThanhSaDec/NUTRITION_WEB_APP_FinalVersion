from __future__ import annotations
import os
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, Optional

from supabase import create_client, Client

# SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "food-uploads")


class SupabaseService:
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Profiles
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            # Avoid 406 from maybe_single by using list semantics
            res = self.client.table('profiles').select('*').eq('user_id', user_id).limit(1).execute()
        except Exception:
            res = None
        if not res:
            return None
        data = getattr(res, 'data', None)
        if not data:
            return None
        if isinstance(data, list):
            return data[0] if data else None
        return data

    def upsert_profile(self, user_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"user_id": user_id, **fields}
        try:
            res = self.client.table('profiles').upsert(payload, on_conflict='user_id').execute()
        except Exception:
            res = None
        if not res or not getattr(res, 'data', None):
            return payload
        data = res.data
        if isinstance(data, list):
            return data[0] if data else payload
        return data or payload

    # Users (app-level table)
    def upsert_user(self, user_id: str, email: Optional[str] = None, display_name: Optional[str] = None, url_image: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {"user_id": user_id}
            if email:
                payload["email"] = email
            if display_name:
                payload["display_name"] = display_name
            if url_image:
                payload["url_image"] = url_image
            res = self.client.table('users').upsert(payload, on_conflict='user_id').execute()
            data = getattr(res, 'data', None)
            if isinstance(data, list):
                return data[0] if data else None
            return data
        except Exception:
            # Non-fatal; table may not exist or policy may block in non-service contexts
            return None

    # Logs
    def insert_food_log(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert one food log and return the inserted row.
        Raises an exception if insertion fails so caller can surface error.
        """
        # For supabase-py v2, insert(...).execute() returns the inserted rows in res.data
        res = self.client.table('food_logs').insert(record).execute()
        data = getattr(res, 'data', None)
        if isinstance(data, list):
            return data[0] if data else {}
        return data or {}

    def get_food_logs_by_day(self, user_id: str, d: date):
        """Fetch logs for a given calendar day in the SERVER'S LOCAL TIMEZONE.
        We compute local [d 00:00, (d+1) 00:00) and convert to UTC for the query,
        then filter the results again in Python to exactly match the local date.
        This avoids off-by-hours issues between local tz and Supabase UTC timestamps.
        """
        local_tz = datetime.now().astimezone().tzinfo
        start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=local_tz)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)
        start = start_utc.isoformat()
        end = end_utc.isoformat()
        try:
            res = (self.client.table('food_logs').select('*')
                   .eq('user_id', user_id)
                   .gte('created_at', start)
                   .lt('created_at', end)
                   .order('created_at', desc=False).execute())
        except Exception:
            res = None
        if not res:
            return []
        rows = getattr(res, 'data', []) or []
        # Secondary filter by local date, to be precise
        out = []
        for r in rows:
            ts = r.get('created_at')
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(str(ts))
                if dt.tzinfo is None:
                    # Assume UTC if tz missing
                    dt = dt.replace(tzinfo=timezone.utc)
                d_local = dt.astimezone(local_tz).date()
                if d_local == d:
                    out.append(r)
            except Exception:
                # If parse fails, include row to avoid dropping data
                out.append(r)
        return out

    # Daily summaries
    def upsert_daily_summary(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            res = self.client.table('daily_summaries').upsert(record, on_conflict='user_id,day').execute()
        except Exception:
            res = None
        if not res or not getattr(res, 'data', None):
            return record
        data = res.data
        if isinstance(data, list):
            return data[0] if data else record
        return data or record

    # Storage
    def upload_image(self, user_id: str, content: bytes, filename: str) -> str:
        ext = (os.path.splitext(filename)[1] or '.jpg').lower()
        key = f"{user_id}/{uuid.uuid4().hex}{ext}"
        # Determine MIME type
        if ext in ('.jpg', '.jpeg'):
            mime = 'image/jpeg'
        elif ext == '.png':
            mime = 'image/png'
        elif ext == '.gif':
            mime = 'image/gif'
        else:
            mime = 'application/octet-stream'

        # storage v2 expects camelCase options; some clients treat values as encoded form fields
        # Use strings for booleans to avoid encode() on bool errors in older versions
        opts = {"contentType": mime, "upsert": "true", "cacheControl": "3600"}

        # Some versions of supabase-py expect a filesystem path for `file`.
        # Write to a temporary file, then upload using that path.
        import tempfile
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(content)
                tmp.flush()
                tmp_path = tmp.name
            # Try common keyword order
            try:
                self.client.storage.from_(SUPABASE_BUCKET).upload(path=key, file=tmp_path, file_options=opts)
            except Exception:
                # Fallback to alternate keyword order
                self.client.storage.from_(SUPABASE_BUCKET).upload(file=tmp_path, path=key, file_options=opts)
        except Exception as e:
            raise RuntimeError(f"Supabase storage upload failed: {e}")
        finally:
            # Clean up temp file
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

        public = self.client.storage.from_(SUPABASE_BUCKET).get_public_url(key)
        # supabase-py v2 returns { 'data': { 'publicUrl': '...' } }
        if isinstance(public, dict):
            data = public.get('data') if isinstance(public.get('data'), dict) else public
            url = None
            if isinstance(data, dict):
                url = data.get('publicUrl') or data.get('public_url')
            return url or ''
        # Fallback: ensure string
        return str(public)


_singleton: Optional[SupabaseService] = None

def get_supabase_service() -> SupabaseService:
    global _singleton
    if _singleton is None:
        _singleton = SupabaseService()
    return _singleton
