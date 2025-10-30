from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin  # For user session support
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import url_for

db = SQLAlchemy()

class User(UserMixin, db.Model):  # UserMixin adds login features
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='developer')  # 'developer' or 'investor'
    company_name = db.Column(db.String(150), nullable=True)
    company_website = db.Column(db.String(255), nullable=True)
    company_address = db.Column(db.String(300), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    surname = db.Column(db.String(100), nullable=True)
    aum = db.Column(db.Float, nullable=True)  # in millions or your preferred unit

    # Projects relationship (one user has many projects)
    projects = db.relationship('Project', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # New: Links to user

    def __repr__(self):
        return f'<Project {self.title}>'

    @property
    def attachment_url(self):
        if self.attachment_path:
            return url_for('uploaded_file', filename=self.attachment_path)
        return None