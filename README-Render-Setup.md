# Render + GitHub Setup (Step-by-step)

## 0) Prereqs
- Python 3.11 locally (or update runtime.txt to your version)
- A GitHub account
- Render account (free)

## 1) Prepare your repo
Ensure your project has:
- `requirements.txt` including `gunicorn` (and `psycopg2-binary` if you plan to use Postgres soon).
- `app.py` exposes `app` (Flask instance): `app = Flask(__name__)`

Copy files from this folder into your project root:
- `Procfile`
- `runtime.txt`
- `render.yaml`
- `.gitignore` (merge with your existing one if present)

Optional DB config tweak: see `app_db_env_snippet.py` or `patch-app-db.diff` in this folder.

## 2) Create GitHub repo & push
From your project root on your Mac:
```bash
git init
git add .
git commit -m "Prepare for Render deploy"
git branch -M main
# Create an empty repo on GitHub first (no README), then:
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## 3) Create Web Service on Render
- Render Dashboard → **New** → **Web Service** → connect GitHub → pick your repo.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
- **Environment Variables**:
  - `SECRET_KEY` = (any strong random string)
  - (Later) `DATABASE_URL` will be auto-set if you attach Render PostgreSQL

Click **Create Web Service** and let the build finish.

## 4) Test & iterate
- Visit the Render URL → log in with your app’s auth.
- Dev loop: edit locally → `git commit -am "msg"` → `git push` → Render auto-deploys.

## 5) Optional: attach Postgres (for persistent data)
- Render → **New** → **PostgreSQL** (Free).
- After created, copy the Internal Connection string.
- Web Service → **Environment** → add `DATABASE_URL` with that value → redeploy.

## 6) Tips
- Free plan sleeps on inactivity; first hit may be slow.
- Filesystem is ephemeral; avoid storing uploads locally.
- Pin Python version in `runtime.txt` (change if your local Python differs).
- Check Logs in Render if a deploy fails.
