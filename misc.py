from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
    
    
    


from app import app, db
from models import Project  # Adjust if your models import differs

with app.app_context():
    all_projects = Project.query.all()
    print(f"Total projects: {len(all_projects)}")
    for proj in all_projects:
        print(f"ID: {proj.id}, Title: {proj.title}, Description: {proj.description[:50]}..., Location: {proj.location}")


# DB UPDATE
# # Create and apply a migration (data preserved)
# # First time only (creates migration folder):
# !flask db init


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


