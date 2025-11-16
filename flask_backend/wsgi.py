from flask_backend.app.flask_app import create_app

# WSGI entrypoint for Gunicorn (app object)
app = create_app()
