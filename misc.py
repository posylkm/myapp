from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
    
    
    


from app import app, db
from models import db, Project, User, NDARequest, CallbackRequest

with app.app_context():
    all_projects = Project.query.all()
    print(f"Total projects: {len(all_projects)}")
    for proj in all_projects:
        print(f"ID: {proj.id}, Title: {proj.title}, Description: {proj.description[:50]}..., Location: {proj.location}")



with app.app_context():
    all_projects = Project.query.all()
    print(f"\n=== PROJECTS ({len(all_projects)}) ===")

    for proj in all_projects:
        print(f"ID: {proj.id}")
        print(f"  Title: {proj.title}")
        print(f"  Type: {proj.project_type}")
        print(f"  Location: {proj.location}")
        print(f"  Budget: {proj.budget}")
        print(f"  Funding: {proj.funding}")
        print(f"  IRR: {proj.irr}")
        print(f"  Owner: User {proj.user_id}")
        print(f"  Description: {proj.description[:80]}...\n")

with app.app_context():
    all_users = User.query.all()
    print(f"\n=== USERS ({len(all_users)}) ===")

    for u in all_users:
        print(f"ID: {u.id}")
        print(f"  Email: {u.email}")
        print(f"  Role: {u.role}")
        print(f"  First: {u.first_name}")
        print(f"  Surname: {u.surname}")
        print(f"  Company: {u.company_name}")
        print(f"  Website: {u.company_website}")
        print(f"  Phone: {u.phone}")
        print(f"  AUM: {u.aum}")
        print(f"  Created: {u.created_at if hasattr(u,'created_at') else '—'}\n")

with app.app_context():
    callbacks = CallbackRequest.query.order_by(CallbackRequest.timestamp.desc()).all()
    print(f"\n=== CALLBACK REQUESTS ({len(callbacks)}) ===")

    for cb in callbacks:
        print(f"ID: {cb.id}")
        print(f"  Name: {cb.name}")
        print(f"  Company: {cb.company}")
        print(f"  Email: {cb.email}")
        print(f"  Phone: {cb.phone}")
        print(f"  Message: {cb.message[:80] if cb.message else ''}")
        print(f"  Timestamp: {cb.timestamp}\n")
        
       

# # Every time you change models:
# !flask db migrate -m "Add callback table to db"
# !flask db upgrade



# PUSH TO GIT
# !git add .
# !git commit -m "callback added"
# !git push



# # Quick backup (just in case)
# SQLite (local):
# sqlite3 instance/projects.db ".backup 'backups/projects-before-$(date +%F-%H%M).db'"
# # Postgres (Render):
# pg_dump "$DATABASE_URL" -Fc -f "backups/prod-before-$(date +%F-%H%M).dump"


# # for Render: set your start command to run migrations automatically:
# flask db upgrade && gunicorn app:app --bind 0.0.0.0:$PORT

# DB UPDATE
# # Create and apply a migration (data preserved)
# # First time only (creates migration folder):
# !flask db init


# # REGISTER ADMIN
# Make sure your virtual environment is active:
# source venv/bin/activate
# python
# and then:
from app import app, db, User

with app.app_context():
    u = User.query.filter_by(email="michael.posylkin@gmail.com").first()
    u.role = "admin"
    db.session.commit()
    print("✅ User promoted to admin!")