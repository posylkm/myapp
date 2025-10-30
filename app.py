from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Project, User
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional, URL, Length, Regexp
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os


def can_edit_project(project, user):
    """Allow editing if user is admin or the developer who owns the project."""
    if not user.is_authenticated:
        return False
    if getattr(user, "role", None) == "admin":
        return True
    return getattr(user, "role", None) == "developer" and project.user_id == user.id


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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if not auth'd
login_manager.login_message = 'Login required to access this page.'

# Add admin and Restrict admin access
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"
    def inaccessible_callback(self, name, **kwargs):
        abort(403)

# Create exactly once:
admin = Admin(app, name="Admin Dashboard")  # endpoint defaults to "admin", url defaults to "/admin"
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Project, db.session))



# class ReadOnlyModelView(SecureModelView):
#     can_create = False
#     can_edit = False
#     can_delete = False

# admin.add_view(ReadOnlyModelView(Project, db.session))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegistrationForm(FlaskForm):
    # Keep new fields Optional until the template renders them
    first_name = StringField("First Name", validators=[Optional(), Length(max=100)])
    surname = StringField("Surname", validators=[Optional(), Length(max=100)])

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])

    role = SelectField(
        "Role",
        choices=[("developer", "Developer"), ("investor", "Investor")],
        validators=[DataRequired()],
    )

    company_name = StringField("Company Name", validators=[Optional(), Length(max=150)])
    company_website = StringField("Company Website", validators=[Optional(), Length(max=255)])
    company_address = StringField("Company Address", validators=[Optional(), Length(max=300)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    aum = FloatField("Assets Under Management (AUM, in millions)", validators=[Optional()])  # investors only

    submit = SubmitField("Register")




class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    
        
class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Project Synopsis/Description', validators=[DataRequired()])
    timeline = TextAreaField('Project Timeline (Optional)', validators=[Optional()])
    exit_strategy = TextAreaField('Project Exit Strategy (Optional)', validators=[Optional()])


    developer_tr = TextAreaField('Developer Track Record (Yrs)', validators=[Optional()])
    website = TextAreaField('Developer Website (Optional)', validators=[Optional()])
    preapproved_facility = TextAreaField('Preapproved Facility (Optional)', validators=[Optional()])
    brand_partnership = TextAreaField('Brand Partnership (Optional)', validators=[Optional()])
    MOIC_EM = TextAreaField('MOIC/EM (Optional)', validators=[Optional()])
    sponsor_equity = FloatField("Sponsor's Equity (%)", validators=[DataRequired(), NumberRange(min=0, max=100)])
    # sponsor_equity = TextAreaField('Sponsor Equity', validators=[Optional(), NumberRange(min=0, max=100, message="Use 0–100")])
    project_type = SelectField('Project Type', choices=[('Residential', 'Residential'), ('commercial', 'Commercial'), ('industrial', 'Industrial')], default='commercial', validators=[DataRequired()])
    budget = FloatField('Budget (USD Millions)', validators=[DataRequired()])
    funding = FloatField('Funding Required (USD Millions)', validators=[Optional()])
    duration = IntegerField('Funding Duration (Months)', validators=[DataRequired()])
    irr = FloatField('Expected IRR', validators=[Optional(), NumberRange(min=0, max=100, message="Use 0–100")])
    location = StringField('Location', validators=[Optional()])
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


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if request.method == "POST":
        current_app.logger.debug(f"/register POST data: {request.form}")

    if form.validate_on_submit():
        # (Optional) role-based requirements – enable later if you want
        if form.role.data == "developer" and not form.company_name.data:
            flash("Please provide Company Name for developers.", "warning")
            return render_template("register.html", form=form)
        if form.role.data == "investor" and not form.aum.data:
            flash("Please provide AUM for investors.", "warning")
            return render_template("register.html", form=form)

        site = (form.company_website.data or "").strip()
        if site and not site.startswith(("http://", "https://")):
            site = "https://" + site

        user = User(
            first_name=(form.first_name.data or None),
            surname=(form.surname.data or None),
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            company_name=(form.company_name.data or None),
            company_website=(site or None),
            company_address=(form.company_address.data or None),
            phone=(form.phone.data or None),
            aum=(form.aum.data if form.aum.data is not None else None),
        )

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("This email is already registered.", "danger")
            return render_template("register.html", form=form)

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    # When validation fails, print and show a friendly message
    if request.method == "POST":
        current_app.logger.debug(f"form.errors: {form.errors}")
        flash("Please correct the highlighted errors and try again.", "warning")

    return render_template("register.html", form=form)


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

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'developer':
        flash('Only developers can upload projects!')
        return redirect(url_for('search'))
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            timeline=form.timeline.data,
            exit_strategy=form.exit_strategy.data,
            developer_tr=form.developer_tr.data,            
            website=form.website.data,            
            preapproved_facility=form.preapproved_facility.data,            
            brand_partnership=form.brand_partnership.data,
            MOIC_EM=form.MOIC_EM.data,
            sponsor_equity=form.sponsor_equity.data,
            project_type=form.project_type.data,
            budget=form.budget.data,
            funding=form.funding.data,  # Add this
            irr=form.irr.data,          # Add this
            duration=form.duration.data,
            location=form.location.data,
            risk_level=form.risk_level.data,
            secured=form.secured.data,
            user_id=current_user.id
        )
        if form.attachment.data and allowed_file(form.attachment.data.filename):
            filename = secure_filename(form.attachment.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.attachment.data.save(filepath)
            project.attachment_path = filename
        db.session.add(project)
        db.session.commit()
        flash('Project uploaded successfully!')
        return redirect(url_for('search'))
    return render_template('upload.html', form=form)



@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not can_edit_project(project, current_user):
        abort(403)

    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        website_value = form.website.data.strip() if form.website.data else None
        if website_value and not website_value.startswith(("http://", "https://")):
            website_value = "https://" + website_value

        # update fields
        project.title = form.title.data
        project.description = form.description.data
        project.project_type = form.project_type.data
        project.budget = form.budget.data
        project.funding = form.funding.data
        project.duration = form.duration.data
        project.irr = form.irr.data
        project.location = form.location.data
        project.risk_level = form.risk_level.data
        project.secured = form.secured.data

        project.timeline = form.timeline.data
        project.exit_strategy = form.exit_strategy.data
        project.developer_tr = form.developer_tr.data
        project.website = website_value
        project.preapproved_facility = form.preapproved_facility.data
        project.brand_partnership = form.brand_partnership.data
        project.MOIC_EM = form.MOIC_EM.data
        project.sponsor_equity = form.sponsor_equity.data

        if form.attachment.data and hasattr(form.attachment.data, "filename") and form.attachment.data.filename:
            if allowed_file(form.attachment.data.filename):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = secure_filename(form.attachment.data.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                form.attachment.data.save(filepath)
                project.attachment_path = filename

        db.session.commit()
        flash("Project updated", "success")
        return redirect(url_for("project_detail", project_id=project.id))

    # 👇 Reuse upload.html; just tell it we’re in edit mode
    return render_template("upload.html", form=form, edit_mode=True, project=project)





@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    # (Optional) if you want only certain roles to view details, enforce here.
    return render_template("project_detail.html", project=project)


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