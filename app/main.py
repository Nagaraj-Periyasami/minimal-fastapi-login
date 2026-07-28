from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .db import init_db, get_conn
from .auth import (
    hash_password,
    verify_password,
    create_session,
    delete_session,
    get_user_by_session,
)

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

SESSION_COOKIE_NAME = "session_id"


@app.on_event("startup")
def _startup():
    init_db()


def current_user(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    return get_user_by_session(session_id)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
def register(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()

    if len(password) < 6:
        return RedirectResponse("/register?error=Password%20must%20be%20at%20least%206%20chars", status_code=303)

    password_hash = hash_password(password)

    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            conn.commit()
    except Exception:
        # keep minimal; could check for unique violation specifically
        return RedirectResponse("/register?error=Email%20already%20registered", status_code=303)

    return RedirectResponse("/login?message=Registered%20successfully.%20Please%20log%20in.", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    error = request.query_params.get("error")
    message = request.query_params.get("message")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error, "message": message},
    )


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()

    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse("/login?error=Invalid%20email%20or%20password", status_code=303)

    session_id = create_session(user["id"])

    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login?error=Please%20log%20in", status_code=303)

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user},
    )


@app.get("/logout")
def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        delete_session(session_id)

    resp = RedirectResponse("/login?message=Logged%20out", status_code=303)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp


# Optional: show register errors cleanly
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "error": error})
