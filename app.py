from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, current_app, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, Project, User, NDARequest, CallbackRequest
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField, PasswordField, SelectField, Form, SelectMultipleField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional, Length
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func, desc
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from forms import ProfileForm
import os


def can_edit_project(project, user):
    if not user.is_authenticated:
        return False
    if getattr(user, "role", None) == "admin":
        return True
    return getattr(user, "role", None) == "developer" and project.user_id == user.id


app = Flask(__name__, instance_relative_config=True)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
else:
    app.config.from_mapping(
        SECRET_KEY='dev-secret-change-me',
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

# Add admin and Restrict admin access
class SecureModelView(ModelView):
    def is_accessible(self):
        return (current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin')

    def inaccessible_callback(self, name, **kwargs):
        flash("Admin area — please log in with an admin account.", "warning")
        return redirect(url_for('login', next=request.url))



# class MyAdminIndexView(AdminIndexView):
#     @expose('/')
#     def index(self):
#         # When someone clicks the Admin’s index (brand or first menu item),
#         # take them to your custom admin dashboard route
#         return redirect(url_for('admin_dashboard'))

#     def is_accessible(self):
#         return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'

# # Create Admin with the index view *named* "Admin Dashboard"
# admin = Admin(
#     app,
#     name="Admin",  # this is just the brand label
#     index_view=MyAdminIndexView(name="Admin Dashboard")
# )



# Create exactly once:
admin = Admin(app, name="")  # endpoint defaults to "admin", url defaults to "/admin"
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Project, db.session))
admin.add_view(SecureModelView(NDARequest, db.session))
admin.add_view(SecureModelView(CallbackRequest, db.session))
admin.add_link(MenuLink(name='Back to Site', url='/'))

migrate = Migrate(app, db)

# class ReadOnlyModelView(SecureModelView):
#     can_create = False
#     can_edit = False
#     can_delete = False

# admin.add_view(ReadOnlyModelView(Project, db.session))

# class MyAdminIndexView(AdminIndexView):
#     @expose("/")
#     def index(self):
#         return redirect(url_for("admin_dashboard"))

#     def is_accessible(self):
#         return current_user.is_authenticated and getattr(current_user, "role", "") == "admin"


# # IMPORTANT: ensure you don't also create another Admin(...) elsewhere
# admin = Admin(
#     app,
#     name="Admin",
#     index_view=MyAdminIndexView(name="Home", endpoint="flask_admin", url="/flask-admin")
# )

# class SearchForm(FlaskForm):      # <-- inherit FlaskForm
#     query = StringField("Query", validators=[Optional()])
#     countries = SelectMultipleField("Countries", validators=[Optional()], coerce=str)
#     submit = SubmitField("Search")

class SearchForm(FlaskForm):
    query = StringField("Query", validators=[Optional()])
    countries = SelectMultipleField("Countries", validators=[Optional()], coerce=str)
    location_type = SelectField(
        "Location Type",
        choices=[("", "Any"), ("prime", "Prime"), ("non-prime", "Non-Prime")],
        validators=[Optional()]
    )
    irr = FloatField("Minimum IRR (%)", validators=[Optional()])
    submit = SubmitField("Search")
    

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
    position_in_company = StringField("Position in Company", validators=[Optional(), Length(max=50)])
    company_website = StringField("Company Website", validators=[Optional(), Length(max=255)])
    company_address = StringField("Company Address", validators=[Optional(), Length(max=300)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    aum = FloatField("Assets Under Management (AUM, in millions)", validators=[Optional()])  # investors only

    submit = SubmitField("Register")




class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# helper to convert "" to None for optional numeric fields    
_blank_none = [lambda v: (v if v not in ("", None) else None)]  
      
class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Project Synopsis/Description', validators=[DataRequired()])
    timeline = TextAreaField('Project Timeline (Optional)', validators=[Optional()])
    exit_strategy = TextAreaField('Project Exit Strategy (Optional)', validators=[Optional()])

    developer_tr = StringField('Developer Track Record (Yrs)', validators=[Optional()])
    website = StringField('Developer Website (Optional)', validators=[Optional()])
    preapproved_facility = StringField('Preapproved Facility (Optional)', validators=[Optional()])
    brand_partnership = StringField('Brand Partnership (Optional)', validators=[Optional()])
    MOIC_EM = StringField('MOIC/EM (Optional)', validators=[Optional()])
    sponsor_equity = FloatField("Sponsor's Equity (%)", validators=[DataRequired(), NumberRange(min=0, max=100)])
    project_type = SelectField('Project Type', choices=[('Residential', 'Residential'), ('commercial', 'Commercial'), ('industrial', 'Industrial')], default='commercial', validators=[DataRequired()])
    budget = FloatField('Budget (USD Millions)', validators=[DataRequired()])
    funding = FloatField('Funding Required (USD Millions)', validators=[Optional()])
    duration = IntegerField('Funding Duration (Months)', validators=[DataRequired()])
    irr = FloatField('Expected IRR', validators=[Optional(), NumberRange(min=0, max=100, message="Use 0–100")])
    location = StringField('Location', validators=[Optional()])
    location_type = SelectField('Location Type', choices=['prime', 'non-prime'], default='prime', validators=[DataRequired()])
    risk_level = IntegerField('Risk Level (1-10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    secured = SelectField('Funding Waterfall', choices=['Equity', 'Mezz','Senior','Negotiable (TBD)'], default='Mezz', validators=[Optional()])                                                      
    attachment = FileField('Upload Attachment (PDF, XLSX, etc.)', validators=[
        FileAllowed({'pdf', 'xlsx', 'xls', 'docx', 'txt', 'png', 'jpg', 'jpeg'}, 'Invalid file type!')
    ])  # FileRequired() if mandatory
    submit = SubmitField('Upload Project')


class NDARequestForm(FlaskForm):
    project_id = HiddenField(validators=[Optional()])
    company = StringField("Your Company", validators=[DataRequired(), Length(max=150)])
    contact_name = StringField("Your Name", validators=[DataRequired(), Length(max=100)])
    contact_email = StringField("Your Email", validators=[DataRequired(), Email(), Length(max=255)])
    message = TextAreaField("Message (optional)", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Submit NDA Request")



# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')


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
            position_in_company=(form.position_in_company.data or None),
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



@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if form.validate_on_submit():
        # Simple columns
        current_user.first_name = form.first_name.data
        current_user.surname = form.surname.data
        current_user.phone = form.phone.data
        current_user.company_name = form.company_name.data
        current_user.position_in_company = form.position_in_company.data
        current_user.company_website = form.company_website.data
        current_user.company_address = form.company_address.data
        current_user.aum = form.aum.data

        # Preferences in JSON
        prefs = current_user.get_preferences()
        prefs.update({
            "preferred_asset_classes": form.preferred_asset_classes.data or "",
            "location_type_preference": form.location_type_preference.data or "",
            "target_min_irr": form.target_min_irr.data or "",
            "ticket_min": form.ticket_min.data or "",
            "ticket_max": form.ticket_max.data or "",
            "email_updates": bool(form.email_updates.data),
        })
        current_user.set_preferences(prefs)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for('profile'))

    # Prefill on GET
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.surname.data = current_user.surname
        form.phone.data = current_user.phone
        form.company_name.data = current_user.company_name
        form.position_in_company.data = current_user.position_in_company
        form.company_website.data = current_user.company_website
        form.company_address.data = current_user.company_address
        form.aum.data = current_user.aum

        prefs = current_user.get_preferences()
        form.preferred_asset_classes.data = prefs.get("preferred_asset_classes", "")
        form.location_type_preference.data = prefs.get("location_type_preference", "")
        form.target_min_irr.data = prefs.get("target_min_irr", "")
        form.ticket_min.data = prefs.get("ticket_min", "")
        form.ticket_max.data = prefs.get("ticket_max", "")
        form.email_updates.data = bool(prefs.get("email_updates", False))

    return render_template('profile.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # user = User.query.filter_by(email=form.email.data).first()
        user = User.query.filter(
            db.func.lower(User.email) == form.email.data.lower()
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('home'))
        flash('Invalid email or password!')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role not in ("developer", "admin"):
        flash("Only developers or admins can upload projects!")
        return redirect(url_for('search'))
    form = ProjectForm()
    if form.validate_on_submit():
        website_value = form.website.data.strip() if form.website.data else None
        if website_value and not website_value.startswith(("http://", "https://")):
            website_value = "https://" + website_value

        project = Project(
            title=form.title.data,
            description=form.description.data,
            timeline=form.timeline.data,
            exit_strategy=form.exit_strategy.data,
            developer_tr=form.developer_tr.data,            
            website=website_value,            
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
            location_type=form.location_type.data,
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
        project.location_type = form.location_type.data
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



# @app.route("/projects/<int:project_id>")
# @login_required
# def project_detail(project_id):
#     project = Project.query.get_or_404(project_id)
#     # (Optional) if you want only certain roles to view details, enforce here.
#     return render_template("project_detail.html", project=project)

@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)  # prefill with existing values
    return render_template("upload.html", form=form, project=project, view_mode=True)



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()

    # build choices dynamically
    rows = db.session.query(Project.location)\
                     .filter(Project.location.isnot(None))\
                     .distinct().order_by(Project.location).all()
    form.countries.choices = [(r[0], r[0]) for r in rows]

    query_text = ""
    selected_countries = []

    if form.validate_on_submit():          # works now because FlaskForm
        query_text = (form.query.data or "").strip()
        selected_countries = form.countries.data or []
        filters = []
        if query_text:
            like = f"%{query_text}%"
            filters.append(or_(
                Project.title.ilike(like),
                Project.description.ilike(like),
                Project.location.ilike(like)
            ))
            
        if form.irr.data:
            filters.append(Project.irr >= form.irr.data)
    
        if form.location_type.data:
            filters.append(Project.location_type == form.location_type.data)
            
        if selected_countries:
            filters.append(Project.location.in_(selected_countries))

        projects = Project.query.filter(*filters).order_by(Project.id.desc()).all() if filters \
                   else Project.query.order_by(Project.id.desc()).all()
    else:
        # initial GET or invalid POST: keep selections if any
        if request.method == "POST":
            query_text = (form.query.data or "").strip()
            selected_countries = form.countries.data or []
        projects = Project.query.order_by(Project.id.desc()).all()

    # ensure selected items stay highlighted in the multi-select
    form.countries.data = selected_countries

    return render_template("search.html", form=form, projects=projects, query=query_text)


@app.route("/eligibility")
def eligibility():
    return render_template("eligibility.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


@app.route("/nda/request", methods=["GET", "POST"])
@login_required
def nda_request():
    form = NDARequestForm()

    # Pre-fill project_id if linked from project page (?project_id=123)
    if request.method == "GET" and "project_id" in request.args:
        form.project_id.data = request.args.get("project_id")

    # Optional: pre-fill known user info if you store it on the user profile
    try:
        if request.method == "GET":
            if hasattr(current_user, "company_name") and current_user.company_name:
                form.company.data = current_user.company_name
            if hasattr(current_user, "first_name") and hasattr(current_user, "surname"):
                full_name = f"{current_user.first_name or ''} {current_user.surname or ''}".strip()
                if full_name:
                    form.contact_name.data = full_name
            if hasattr(current_user, "email") and current_user.email:
                form.contact_email.data = current_user.email
    except Exception:
        pass  # keep it resilient even if fields don't exist

    if form.validate_on_submit():
        # --- Option A: no DB yet (simple log + flash) ---
        # current_app.logger.info(
        #     "NDA_REQUEST user_id=%s project_id=%s company=%s name=%s email=%s msg_len=%s",
        #     getattr(current_user, "id", None),
        #     form.project_id.data or "",
        #     form.company.data,
        #     form.contact_name.data,
        #     form.contact_email.data,
        #     len(form.message.data or "")
        # )
        # --- Option B: save to DB ---
        req = NDARequest(
            user_id=current_user.id,
            project_id=int(form.project_id.data) if form.project_id.data else None,
            company=form.company.data,
            contact_name=form.contact_name.data,
            contact_email=form.contact_email.data,
            message=form.message.data or None
        )
        db.session.add(req)
        db.session.commit()
        # flash("Thanks — your NDA request has been submitted.", "success")

        # If you have email integration later, trigger it here.
        # e.g. send to admin/dev team.

        flash("Thanks — your NDA request has been received. We’ll follow up shortly.", "success")

        # Redirect back to project if provided, otherwise to Home
        if form.project_id.data:
            try:
                return redirect(url_for("project_detail", project_id=int(form.project_id.data)))
            except Exception:
                pass
        return redirect(url_for("home"))

    return render_template("nda_request.html", form=form)


@app.route("/callback", methods=["GET", "POST"])
def request_callback():
    from flask import request

    if request.method == "POST":
        name = request.form.get("name")
        company = request.form.get("company")
        phone = request.form.get("phone")
        email = request.form.get("email")
        message = request.form.get("message")

        # Log or handle the data (later can save to DB or email)
        # app.logger.info(f"Callback request: {name} | {company} | {email} | {phone} | {message}")
        new_request = CallbackRequest(
        name=name,
        company=company,
        email=email,
        phone=phone,
        message=message
        )
        db.session.add(new_request)
        db.session.commit()

        flash("Thank you — our team will contact you shortly.", "success")
        return redirect(url_for("faq"))

    return render_template("callback.html")


@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    # gate: admin only
    if getattr(current_user, "role", "") != "admin":
        flash("Admin only.", "warning")
        return redirect(url_for("home"))

    # --- Aggregates / counts ---
    users_count = db.session.query(func.count(User.id)).scalar()
    projects_count = db.session.query(func.count(Project.id)).scalar()

    # If CallbackRequest model exists; otherwise set to 0
    try:
        callbacks_count = db.session.query(func.count(CallbackRequest.id)).scalar()
    except Exception:
        callbacks_count = 0

    # If NDARequest model exists; otherwise set to 0
    try:
        nDAs_count = db.session.query(func.count(NDARequest.id)).scalar()
    except Exception:
        nDAs_count = 0


    # --- Recent items (top 10) ---
    recent_users = User.query.order_by(desc(User.id)).limit(10).all()
    recent_projects = Project.query.order_by(desc(Project.id)).limit(10).all()
    try:
        recent_callbacks = CallbackRequest.query.order_by(desc(CallbackRequest.timestamp)).limit(10).all()
    except Exception:
        recent_callbacks = []
        
    
    try:
        recent_NDA_Requests = NDARequest.query.order_by(desc(NDARequest.created_at)).limit(10).all()
    except Exception:
        recent_NDA_Requests = []


    return render_template(
        "admin_dashboard.html",
        users_count=users_count,
        projects_count=projects_count,
        callbacks_count=callbacks_count,
        nDAs_count=nDAs_count,
        recent_users=recent_users,
        recent_projects=recent_projects,
        recent_callbacks=recent_callbacks,
        recent_NDA_Requests=recent_NDA_Requests,
    )


@app.route("/admin-dashboard/export/users.csv")
@login_required
def export_users_csv():
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    rows = User.query.order_by(User.id).all()
    def gen():
        yield "id,email,role,first_name,surname,company_name,phone,aum\n"
        for u in rows:
            yield f'{u.id},{u.email},{u.role},{u.first_name or ""},{u.surname or ""},{u.company_name or ""},{u.phone or ""},{u.aum or ""}\n'
    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=users.csv"})

@app.route("/admin-dashboard/export/projects.csv")
@login_required
def export_projects_csv():
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    rows = Project.query.order_by(Project.id).all()
    def gen():
        yield "id,title,project_type,location,budget,funding,irr,duration,owner_id\n"
        for p in rows:
            yield f'{p.id},"{p.title}",{p.project_type},{p.location},{p.budget},{p.funding},{p.irr},{p.duration},{p.user_id}\n'
    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=projects.csv"})

@app.route("/admin-dashboard/export/callbacks.csv")
@login_required
def export_callbacks_csv():
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    try:
        rows = CallbackRequest.query.order_by(CallbackRequest.timestamp.desc()).all()
    except Exception:
        rows = []
    def gen():
        yield "id,name,company,email,phone,message,timestamp\n"
        for c in rows:
            msg = (c.message or "").replace('\n', ' ').replace('"','""')
            yield f'{c.id},"{c.name or ""}","{c.company or ""}",{c.email or ""},{c.phone or ""},"{msg}",{c.timestamp}\n'
    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=callbacks.csv"})


@app.route("/admin-dashboard/export/NDAs.csv")
@login_required
def export_NDA_csv():
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    try:
        rows = NDARequest.query.order_by(NDARequest.created_at.desc()).all()
    except Exception:
        rows = []
    def gen():
        yield "id,name,company,email,phone,message,timestamp\n"
        for c in rows:
            msg = (c.message or "").replace('\n', ' ').replace('"','""')
            yield f'{c.user_id},"{c.contact_name or ""}","{c.company or ""}",{c.contact_email or ""},"{msg}",{c.created_at}\n'
    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ndas.csv"})





@app.errorhandler(403)
def forbidden(e):
    flash("You don't have permission to view that page.", "warning")
    return redirect(url_for('home'))


@app.route("/whoami")
def whoami():
    if current_user.is_authenticated:
        return f"Logged in as: {current_user.email} | role={getattr(current_user, 'role', None)}"
    return "Not logged in"


ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False, threaded=True)  # As per previous fix