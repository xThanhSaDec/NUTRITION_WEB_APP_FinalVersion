from __future__ import annotations
import os
from typing import Dict, Any
from pybars import Compiler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")
PAGES_DIR = os.path.join(TEMPLATES_DIR, "pages")
PARTIALS_DIR = os.path.join(TEMPLATES_DIR, "partials")

compiler = Compiler()

# Load and register partials at import time
_partials: Dict[str, Any] = {}
for fname in (os.listdir(PARTIALS_DIR) if os.path.isdir(PARTIALS_DIR) else []):
    if not fname.endswith(".hbs"): continue
    name = fname[:-4]
    with open(os.path.join(PARTIALS_DIR, fname), "r", encoding="utf-8") as f:
        _partials[name] = compiler.compile(f.read())

# Load layout
_layout_tmpl = None
_layout_path = os.path.join(TEMPLATES_DIR, "layout.hbs")
if os.path.exists(_layout_path):
    with open(_layout_path, "r", encoding="utf-8") as f:
        _layout_tmpl = compiler.compile(f.read())


def render_page(page_name: str, context: Dict[str, Any] | None = None) -> str:
    context = context or {}
    page_path = os.path.join(PAGES_DIR, f"{page_name}.hbs")
    if not os.path.exists(page_path):
        return f"<h1>404</h1><p>Template pages/{page_name}.hbs not found.</p>"
    with open(page_path, "r", encoding="utf-8") as f:
        page_tmpl = compiler.compile(f.read())
    # Compose into layout
    body_html = page_tmpl(context, helpers=None, partials=_partials)
    if _layout_tmpl is None:
        # No layout: return the raw body
        return body_html
    # Provide common layout context
    layout_ctx = {
        **context,
        "body": body_html,
        # Static paths
        "styles_href": "/app/styles.css",
        "config_js": "/app/config.js",
        "supabase_js": "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2",
        "chart_js": "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js",
        "handlebars_js": "https://cdn.jsdelivr.net/npm/handlebars@latest/dist/handlebars.js",
    }
    return _layout_tmpl(layout_ctx, helpers=None, partials=_partials)
