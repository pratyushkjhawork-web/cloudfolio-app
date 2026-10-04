# CloudFolio — AI-Assisted Editable Portfolio & Resume Builder

A cloud-native resume builder built for **CSE2025 — AWS Solution Architecture**
(Dr. Renita R., VIT-AP). Users fill out a form, see a live resume preview,
download a polished ATS-friendly PDF, and get AI-powered writing help —
including a job-description match score that tells you how well your
resume fits a specific role. Deployed on AWS using EC2, RDS, S3, VPC,
and IAM.

## Features

- **Resume builder with live preview** — fill in details, see the formatted
  resume update as you type
- **ATS-friendly PDF export** — single-column, parser-safe layout (ReportLab)
- **AI Improve** on every text field — professional summary, each experience
  entry, and each project description can be rewritten by Gemini on demand,
  with a visible word-level diff (added text in green, removed in red) so
  you always see exactly what changed, never a silent swap
- **Job Description Match** — paste a JD, get a 0–100 match score, matched
  vs. missing keywords, and concrete suggestions to improve alignment
- **Save & edit** — resumes persist (SQLite locally, RDS MySQL in the cloud)
  and can be revisited and updated anytime
- **Graceful AI degradation** — every AI feature works (and clearly says so)
  even with no API key configured, and automatically retries + falls back to
  a second model if Gemini is temporarily overloaded, rather than crashing

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Plain HTML/CSS/JS — no build step, served directly by the backend |
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite (local) / RDS MySQL (deployed) — same code, switches via `DATABASE_URL` |
| PDF generation | ReportLab |
| AI | Gemini (`google-genai`), with retry + model fallback on overload |
| Cloud | AWS — EC2, RDS, S3, VPC, Security Groups, IAM, SSM |

## Running it locally

One command, one terminal — the backend serves the frontend directly:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Windows PowerShell:** `python -m uvicorn main:app --reload --port 8000`

Open `http://localhost:8000`. This creates `cloudfolio.db` (SQLite)
automatically on first run — no separate database setup needed for local use.

### Enabling AI features

```bash
cd backend
cp .env.example .env
```

Open `.env` and paste your real Gemini API key in place of `your-key-here`.
`.env` is git-ignored — your key is never committed.

Confirm the backend sees your key (without revealing it) at
`http://localhost:8000/api/ai/status` once the server is running.

## Deploying to AWS

Full deployment scripts live in [`infra/`](infra/) — see
[`infra/README.md`](infra/README.md) for the exact run order and
screenshot checklist.

In short: `infra/01-network-setup.sh` through `04-s3-setup.sh` provision a
VPC/security groups, RDS MySQL, an EC2 instance (which auto-clones this repo
and starts the app via `systemd` on boot), and an S3 bucket — in that order,
using the AWS CLI.

## Project structure

```
cloudfolio-app/
├── backend/
│   ├── main.py              FastAPI app — all routes, serves the frontend too
│   ├── models.py            SQLAlchemy model (resumes table)
│   ├── database.py          DB connection — SQLite locally, RDS MySQL on AWS
│   ├── schemas.py           Pydantic request/response schemas
│   ├── pdf_generator.py     ReportLab PDF generation
│   ├── ai_suggestions.py    Gemini calls — field improvement + JD matching
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js                Form handling, live preview, AI diff rendering
│   └── style.css
├── infra/                    AWS deployment scripts (see infra/README.md)
└── README.md                 This file
```

## AWS architecture & course requirement mapping

| Course Module | Services used |
|---|---|
| Module 1 — Compute & Storage | EC2, S3 (encryption + lifecycle policy) |
| Module 2 — Networking | VPC, Security Groups |
| Module 3 — Databases | RDS (MySQL) |
| Module 4 — IAM & Security | IAM (via Sandbox-provided LabRole/LabInstanceProfile) |

RDS is only reachable from the EC2 instance's security group — never
exposed directly to the internet. EC2 instance access uses AWS Systems
Manager Session Manager rather than SSH key pairs.
