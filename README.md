# CloudFolio — Local App (Phase 1)

AI-assisted, editable portfolio & resume builder — CSE2025 AWS Solution Architecture course project.

This is the **local, pre-AWS version**: FastAPI backend + SQLite + plain HTML/JS
frontend. No authentication (single-user MVP, scoped down for time).
AWS deployment (EC2, RDS, S3, IAM, etc.) comes in Phase 2.

## Running the app (one command, one terminal)

The backend serves the frontend directly — no separate frontend server needed.

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open `http://localhost:8000` in your browser. That's it — one
terminal, one process, both the API and the web page.

This creates `cloudfolio.db` (SQLite) automatically on first run.

**Windows PowerShell users:** the equivalent is
`python -m uvicorn main:app --reload --port 8000` (run from inside `backend`).

### AI suggestions (optional)

The "AI Improve" button calls Gemini. To enable it:

```bash
cd backend
cp .env.example .env
```

Then open `.env` and paste your real key in place of `your-key-here`.
The app loads it automatically on startup — no need to set an
environment variable by hand every time you open a new terminal.

**`.env` is git-ignored** (see `.gitignore`) — never commit your real
key. `.env.example` (no real key inside) is safe to commit and shows
collaborators/graders what variable is expected.

Without a key set, the AI endpoint still works — it just returns your
original text unchanged (no crash), and the diff box in the UI will
tell you plainly that no change was made / to check the key, so the
rest of the app is fully usable without an API key during development.

You can confirm the backend sees your key (without revealing it) by
visiting `http://localhost:8000/api/ai/status` once the server is
running.

## What's here

- `backend/main.py` — FastAPI app, all routes
- `backend/models.py` — SQLAlchemy model (one `resumes` table, JSON columns for list-shaped data)
- `backend/database.py` — DB connection (SQLite now, swap to RDS MySQL later — see comments in file)
- `backend/pdf_generator.py` — ReportLab-based ATS-friendly PDF generation
- `backend/ai_suggestions.py` — Gemini call for the AI-improve feature, with graceful no-op if no API key
- `frontend/` — single-page form + live preview, calls the backend via `fetch`

## Known scope cuts (deliberate, due to time constraints)

- No authentication/login — single implicit user, resume identified by ID
- One resume "template" (the PDF layout in `pdf_generator.py`) rather than 2-3
- No QR code / public sharing / analytics (were "advanced" features, cut for time)
- AI feature is one button (improve summary/experience text), not four

## Next: AWS deployment (Phase 2)

Planned: EC2 (backend), S3 (PDF storage), RDS MySQL (swap out SQLite),
IAM (via AWS Academy Sandbox's provided LabRole — Sandbox restricts
custom IAM policy creation), CloudWatch/CloudTrail, minimal VPC.
Using AWS Academy Cloud Foundations Sandbox, which resets fully at
the end of each session — so infra will be provisioned via scripts
(not manual console clicks) for fast rebuilding each session.
