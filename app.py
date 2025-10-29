from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Project, User
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, instance_relative_config=True)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
# else: keep your local SQLite config as-is

app.config.from_mapping(
    SECRET_KEY='your-secret-key-change-this',
    DATABASE=os.path.join(app.instance_path, 'projects.db'),
)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{app.config["DATABASE"]}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if not auth'd
login_manager.login_message = 'Login required to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('investor', 'Investor'), ('developer', 'Developer')], default='investor')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    
        
class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired()])
    description = TextAreaField('Synopsis/Description', validators=[DataRequired()])
    project_type = SelectField('Project Type', choices=[('Residential', 'Residential'), ('commercial', 'Commercial'), ('industrial', 'Industrial')], default='commercial', validators=[DataRequired()])
    budget = FloatField('Budget (USD Millions)', validators=[DataRequired()])
    funding = FloatField('Funding Required (USD Millions)', validators=[DataRequired()])
    duration = IntegerField('Funding Duration (Months)', validators=[DataRequired()])
    irr = FloatField('Expected IRR', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    risk_level = IntegerField('Risk Level (1-10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    secured = SelectField('Funding Waterfall', choices=['Equity', 'Mezz','Senior','Negotiable (TBD)'], default='Mezz', validators=[DataRequired()])                                                        
    attachment = FileField('Upload Attachment (PDF, XLSX, etc.)', validators=[
        FileAllowed({'pdf', 'xlsx', 'xls', 'docx', 'txt', 'png', 'jpg', 'jpeg'}, 'Invalid file type!')
    ])  # FileRequired() if mandatory
    submit = SubmitField('Upload Project')

# Routes
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered!')
            return render_template('register.html', form=form)
        user = User(email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        flash('Invalid email or password!')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

# @app.route('/upload', methods=['GET', 'POST'])
# @login_required
# def upload():
#     if current_user.role != 'developer':
#         flash('Only developers can upload projects!')
#         return redirect(url_for('search'))
#     form = ProjectForm()
#     if form.validate_on_submit():
#         project = Project(
#             title=form.title.data,
#             description=form.description.data,
#             project_type=form.project_type.data,
#             budget=form.budget.data,
#             funding=form.funding.data,  # Add this
#             irr=form.irr.data,          # Add this
#             duration=form.duration.data,
#             location=form.location.data,
#             risk_level=form.risk_level.data,
#             user_id=current_user.id
#         )
#         if form.attachment.data and allowed_file(form.attachment.data.filename):
#             filename = secure_filename(form.attachment.data.filename)
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             form.attachment.data.save(filepath)
#             project.attachment_path = filename
#         db.session.add(project)
#         db.session.commit()
#         flash('Project uploaded successfully!')
#         return redirect(url_for('search'))
#     return render_template('upload.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'developer':
        flash('Only developers can upload projects!')
        return redirect(url_for('search'))
    form = ProjectForm()
    if form.validate_on_submit():
        print(f"[DEBUG] Form valid! Title: {form.title.data}, User ID: {current_user.id}")  # Add this
        project = Project(
            title=form.title.data,
            description=form.description.data,
            project_type=form.project_type.data,
            budget=form.budget.data,
            funding=form.funding.data,
            irr=form.irr.data,
            duration=form.duration.data,
            location=form.location.data,
            risk_level=form.risk_level.data,
            secured=form.secured.data,
            user_id=current_user.id
        )
        print(f"[DEBUG] Project object created: ID temp={project.id}")  # Add this (ID is None pre-commit)
        if form.attachment.data and allowed_file(form.attachment.data.filename):
            filename = secure_filename(form.attachment.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.attachment.data.save(filepath)
            project.attachment_path = filename
            print(f"[DEBUG] File saved: {filename}")  # Add this
        db.session.add(project)
        db.session.commit()
        print(f"[DEBUG] Committed! New project ID: {project.id}")  # Add this—key check!
        flash('Project uploaded successfully!')
        return redirect(url_for('search'))
    else:
        print(f"[DEBUG] Form errors: {form.errors}")  # Add this for validation fails
    return render_template('upload.html', form=form)




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('query', '') if request.method == 'POST' else ''
    projects = Project.query.all() if not query else Project.query.filter(
        Project.title.contains(query) | Project.description.contains(query) | Project.location.contains(query)
    ).all()
    return render_template('search.html', projects=projects, query=query)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False, threaded=True)  # As per previous fix