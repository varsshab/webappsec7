import hashlib
import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("DATA_DIR", BASE / "data"))
UPLOADS = DATA / "uploads"
PRIVATE = DATA / "private"
DB_PATH = DATA / "dropoff.db"

UPLOADS.mkdir(parents=True, exist_ok=True)
PRIVATE.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dropoff-dev-secret"))
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                display_name TEXT,
                password_hash TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                stored_name TEXT,
                original_name TEXT,
                uploaded_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO users (username, display_name, password_hash) VALUES (?, ?, ?)",
                ("maya", "Maya Chen", hash_password("campus123")),
            )
            conn.execute(
                "INSERT INTO users (username, display_name, password_hash) VALUES (?, ?, ?)",
                ("devon", "Devon Alvarez", hash_password("campus123")),
            )
            maya = conn.execute("SELECT id FROM users WHERE username = 'maya'").fetchone()[0]
            sample = UPLOADS / "lab1-maya.txt"
            sample.write_text("Lab 1: completed the buffer walkthrough. See me if the TA notes disagree.\n")
            conn.execute(
                "INSERT INTO files (user_id, stored_name, original_name) VALUES (?, ?, ?)",
                (maya, "lab1-maya.txt", "lab1-maya.txt"),
            )
    grader = PRIVATE / "grader.txt"
    if not grader.exists():
        grader.write_text(
            "TA only. Makeup window for Lab 2 is Thursday 6pm. Release code DROP-5521. Do not put this in the drop folder.\n"
        )


@app.on_event("startup")
def startup():
    init_db()


def current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return None
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = current_user(request)
    files = []
    if user:
        with db() as conn:
            files = conn.execute(
                "SELECT * FROM files WHERE user_id = ? ORDER BY id DESC", (user["id"],)
            ).fetchall()
    return templates.TemplateResponse(
        "home.html", {"request": request, "user": user, "files": files}
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
        ).fetchone()
    if not user or user["password_hash"] != hash_password(password):
        return RedirectResponse("/login?error=1", status_code=303)
    request.session["user_id"] = user["id"]
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    original = file.filename or "upload.bin"
    stored = original
    dest = UPLOADS / stored
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    with db() as conn:
        conn.execute(
            "INSERT INTO files (user_id, stored_name, original_name) VALUES (?, ?, ?)",
            (user["id"], stored, original),
        )
    return RedirectResponse("/", status_code=303)


@app.get("/download")
def download(name: str):
    path = os.path.join(str(UPLOADS), name)
    if not os.path.isfile(path):
        return HTMLResponse("That file is not in the drop.", status_code=404)
    return FileResponse(path, filename=os.path.basename(name))


@app.get("/health")
def health():
    return {"ok": True}
