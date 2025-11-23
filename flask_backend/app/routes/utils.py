from __future__ import annotations
from flask import abort

def require_fields(data, fields):
    missing = [f for f in fields if f not in data]
    if missing:
        abort(400, f"Missing fields: {', '.join(missing)}")
