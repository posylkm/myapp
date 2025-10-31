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



# PUSH TO GIT
# !git add .
# !git commit -m "more register info & added admin"
# !git push