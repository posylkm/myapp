from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON  # optional fallback
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin  # For user session support
from werkzeug.security import generate_password_hash, check_password_hash
import os, json
from flask import url_for

db = SQLAlchemy()


preferences_json = db.Column(db.Text, nullable=True)   # stores JSON string with preferences
updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class CallbackRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class NDARequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=True)
    company = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='developer')

    company_name = db.Column(db.String(150))
    position_in_company = db.Column(db.String(50))
    company_website = db.Column(db.String(255))
    company_address = db.Column(db.String(300))
    phone = db.Column(db.String(30))
    first_name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    aum = db.Column(db.Float)

    projects = db.relationship('Project', backref='owner', lazy=True)

    # Store all profile preferences here to avoid schema churn
    preferences_json = db.Column(db.JSON, nullable=False, default=dict)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_preferences(self) -> dict:
        prefs = getattr(self, "preferences_json", None)
        if not prefs:
            return {}
        if isinstance(prefs, dict):
            return prefs
        try:
            return json.loads(prefs) if prefs else {}
        except Exception:
            return {}

    def set_preferences(self, prefs: dict) -> None:
        if not isinstance(prefs, dict):
            raise ValueError("prefs must be a dict")
        self.preferences_json = prefs  # <- don't comment this out

    # Convenience getters/setters so you can call user.pref_x like fields
    def _pref_get(self, key, default=None):
        return self.get_preferences().get(key, default)

    def _pref_set(self, key, value):
        prefs = self.get_preferences()
        prefs[key] = value
        self.set_preferences(prefs)

    @hybrid_property
    def preferred_asset_classes(self):
        return self._pref_get("preferred_asset_classes", "")

    @preferred_asset_classes.setter
    def preferred_asset_classes(self, v):
        self._pref_set("preferred_asset_classes", v)

    @hybrid_property
    def location_type_preference(self):
        return self._pref_get("location_type_preference", "")

    @location_type_preference.setter
    def location_type_preference(self, v):
        self._pref_set("location_type_preference", v)

    @hybrid_property
    def target_min_irr(self):
        return self._pref_get("target_min_irr", "")

    @target_min_irr.setter
    def target_min_irr(self, v):
        self._pref_set("target_min_irr", v)

    @hybrid_property
    def email_updates(self):
        return bool(self._pref_get("email_updates", False))

    @email_updates.setter
    def email_updates(self, v):
        self._pref_set("email_updates", bool(v))

    @hybrid_property
    def ticket_min(self):
        return self._pref_get("ticket_min", "")

    @ticket_min.setter
    def ticket_min(self, v):
        self._pref_set("ticket_min", v)

    @hybrid_property
    def ticket_max(self):
        return self._pref_get("ticket_max", "")

    @ticket_max.setter
    def ticket_max(self, v):
        self._pref_set("ticket_max", v)

    def __repr__(self):
        return f'<User {self.email}>'


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    project_type = db.Column(db.String(50), default='commercial')  # e.g., 'residential', 'commercial'
    budget = db.Column(db.Float, nullable=False)
    funding = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=True)
    irr = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    risk_level = db.Column(db.Integer, default=5)  # 1-10 scale
    secured = db.Column(db.String(50), default='mezz')
    attachment_path = db.Column(db.String(300))
    
    timeline = db.Column(db.String(200), nullable=True)
    exit_strategy = db.Column(db.String(200), nullable=True)
    developer_tr = db.Column(db.String(200), nullable=True)  
    website = db.Column(db.String(200), nullable=True)
    preapproved_facility = db.Column(db.String(100), nullable=True)
    brand_partnership = db.Column(db.String(100), nullable=True)
    MOIC_EM = db.Column(db.Float, nullable=True)
    sponsor_equity = db.Column(db.Float, nullable=False)
    location_type = db.Column(db.String(50), default='prime') # e.g., 'prime', 'non-prime'

    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # New: Links to user

    def __repr__(self):
        return f'<Project {self.title}>'

    @property
    def attachment_url(self):
        if self.attachment_path:
            return url_for('uploaded_file', filename=self.attachment_path)
        return None