"""
Flask app factory registering blueprints and serving the Handlebars site.
"""
from __future__ import annotations
#.\.venv\Scripts\Activate.ps1  
#py -m app.flask_app
import os, sys
from flask import Flask, send_from_directory, Response, redirect, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Ensure we always load the project root .env, regardless of current working directory
from dotenv import load_dotenv as _ld
_ld(os.path.join(BASE_DIR, ".env"))


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    # Allow all origins + credentials for Supabase auth cookies/headers; adapt if locking down later.
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Register API blueprints
    from .routes.health import bp as health_bp
    from .routes.predict import bp as predict_bp
    from .routes.user import bp as user_bp
    from .routes.meals import bp as meals_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(meals_bp)

    # Serve static assets under /app/*
    WEB_DIR = os.path.join(BASE_DIR, "web")

    # Render .hbs pages server-side
    from .services.templating import render_page

    @app.get("/")
    def index():
        html = render_page("index", {})
        return Response(html, mimetype="text/html")

    # Legacy static HTML paths -> redirect to SSR routes
    @app.get("/app/<page>.html")
    def legacy_html(page: str):
        mapping = {
            "login": "/login",
            "profile": "/profile",
            "upload": "/upload",
            "today": "/today",
            "history": "/history",
            "index": "/",
            "home": "/",
        }
        target = mapping.get(page)
        if target:
            return redirect(target, code=301)
        return Response("<h1>Not Found</h1>", status=404, mimetype="text/html")

    @app.get("/app/<path:path>")
    def serve_app(path: str):
        return send_from_directory(WEB_DIR, path)

    @app.get("/login")
    def page_login():
        return Response(render_page("login", {}), mimetype="text/html")

    @app.get("/profile")
    def page_profile():
        return Response(render_page("profile", {}), mimetype="text/html")

    @app.get("/account")
    def page_account():
        return Response(render_page("account", {}), mimetype="text/html")

    @app.get("/today")
    def page_today():
        return Response(render_page("today", {}), mimetype="text/html")

    @app.get("/history")
    def page_history():
        return Response(render_page("history", {}), mimetype="text/html")

    @app.get("/statistic")
    def page_statistic():
        return Response(render_page("statistic", {}), mimetype="text/html")

    @app.get("/upload")
    def page_upload():
        return Response(render_page("upload", {}), mimetype="text/html")

    # Global error handlers to ensure API returns JSON on errors
    @app.errorhandler(500)
    def handle_500(err):
        if str(request.path).startswith('/api/'):
            return jsonify({"success": False, "error": "Internal server error"}), 500
        return err

    @app.errorhandler(404)
    def handle_404(err):
        if str(request.path).startswith('/api/'):
            return jsonify({"success": False, "error": "Not found"}), 404
        return err

    return app


# For `python -m flask_backend.app.flask_app`
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
