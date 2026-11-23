# DropOff

Lab submission drop for one section. Students upload a file, keep the original name, and download what they already turned in.

FastAPI, Jinja templates, SQLite, and a folder on disk.

## Features

- Sign in and sign out
- Upload a lab file under its original name
- List and download your own files
- Health check at `/health`

## Run locally

Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 3000
```

Open http://localhost:3000. The database and upload folder are created on first request under `data/`.

## Run with Docker

```bash
docker compose up --build
```

The app listens on port 3000.

## Demo accounts

| Username | Password |
|---|---|
| `maya` | `campus123` |
| `devon` | `campus123` |

Maya already has a sample lab file.

## Project layout

```
app.py              Routes, auth, upload, download
templates/          Pages
static/style.css
data/uploads/       Student files
data/dropoff.db     Users and file rows
```

## Assignment notes

Host this somewhere your classmates and instructor can reach. Walk the running app until you can explain:

- where an uploaded file lands on disk
- how a download request becomes a path
- what a signed-in user can list versus what is only a file on disk
- what is in `data/` after the first request

Then look for a security defect in the running system, document how to trigger it, and patch it without breaking normal upload and download. Submit the hosted URL, a short architecture sketch, the writeup, and the patched repo.
