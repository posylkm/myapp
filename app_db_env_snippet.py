# Drop this snippet into your app.py after you create the Flask app
# and before you initialize the DB (SQLAlchemy). Adjust imports to match your project.

import os

# Example: from models import db
# from models import db

# Ensure you already created the Flask app above:
# app = Flask(__name__, instance_relative_config=True)

# Keep your existing local SQLite config for development.
# This snippet switches to DATABASE_URL (e.g., Render PostgreSQL) when present.

database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Render may provide 'postgres://' which SQLAlchemy expects as 'postgresql://'
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Optional: create tables automatically (fine for a small prototype)
# @app.before_request
# def _create_tables_if_needed():
#     db.create_all()
