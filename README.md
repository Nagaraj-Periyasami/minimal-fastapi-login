# Minimal FastAPI Login (SQLite + HTML)

Minimal login/register/dashboard app using **Python FastAPI** + **SQLite** + **plain HTML**.

- Registration (email + password)
- Login (email + password)
- Protected dashboard
- Server-side sessions stored in SQLite (session_id cookie)

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000

## Routes
- GET/POST `/register`
- GET/POST `/login`
- GET `/dashboard` (requires login)
- GET `/logout`
