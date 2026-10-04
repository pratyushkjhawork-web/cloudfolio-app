"""
CloudFolio backend — FastAPI app.

Routes:
  POST   /api/resumes            create a resume
  GET    /api/resumes/{id}       fetch a resume
  PUT    /api/resumes/{id}       update (edit) a resume
  DELETE /api/resumes/{id}       delete a resume
  GET    /api/resumes/{id}/pdf   download the resume as a PDF
  POST   /api/ai/suggest         get an AI-improved version of a text field

No auth — single-user MVP scope. Add JWT later only if time allows.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db, Base
import models
import schemas
from pdf_generator import generate_resume_pdf
from ai_suggestions import suggest_improvement, analyze_against_jd

# Creates cloudfolio.db and the resumes table on first run, if missing.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CloudFolio API")

# Allow the frontend (served separately, e.g. via `python -m http.server`)
# to call this API during local dev. Tighten this before deploying to AWS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resume_to_dict(resume: models.Resume) -> dict:
    """Flatten a Resume ORM row into the plain dict the PDF generator expects."""
    return {
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "location": resume.location,
        "linkedin": resume.linkedin,
        "github": resume.github,
        "summary": resume.summary,
        "skills": resume.skills or [],
        "experience": resume.experience or [],
        "education": resume.education or [],
        "projects": resume.projects or [],
    }


@app.post("/api/resumes", response_model=schemas.ResumeOut)
def create_resume(resume: schemas.ResumeCreate, db: Session = Depends(get_db)):
    data = resume.model_dump()
    # Pydantic gives us lists of nested models; convert to plain dicts for JSON columns
    data["experience"] = [e for e in data.get("experience", [])]
    data["education"] = [e for e in data.get("education", [])]
    data["projects"] = [e for e in data.get("projects", [])]

    db_resume = models.Resume(**data)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


@app.get("/api/resumes/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@app.put("/api/resumes/{resume_id}", response_model=schemas.ResumeOut)
def update_resume(resume_id: int, resume: schemas.ResumeUpdate, db: Session = Depends(get_db)):
    db_resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    for key, value in resume.model_dump().items():
        setattr(db_resume, key, value)

    db.commit()
    db.refresh(db_resume)
    return db_resume


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(db_resume)
    db.commit()
    return {"detail": "Resume deleted"}


@app.get("/api/resumes/{resume_id}/pdf")
def download_resume_pdf(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    pdf_bytes = generate_resume_pdf(_resume_to_dict(resume))
    filename = f"{resume.full_name.replace(' ', '_')}_resume.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/ai/suggest", response_model=schemas.AISuggestResponse)
def ai_suggest(request: schemas.AISuggestRequest):
    suggestion = suggest_improvement(request.text, request.field_type)
    return schemas.AISuggestResponse(original=request.text, suggestion=suggestion)


def _resume_to_plain_text(resume: models.Resume) -> str:
    """Flattens a resume into plain text for feeding to the JD-matching prompt."""
    lines = [resume.full_name or "", resume.summary or ""]

    skills = resume.skills or []
    if skills:
        lines.append("Skills: " + ", ".join(skills))

    for exp in (resume.experience or []):
        lines.append(f"{exp.get('title', '')} at {exp.get('company', '')}: {exp.get('description', '')}")

    for proj in (resume.projects or []):
        lines.append(f"Project — {proj.get('title', '')}: {proj.get('description', '')}")

    for edu in (resume.education or []):
        lines.append(f"{edu.get('degree', '')} — {edu.get('institution', '')}")

    return "\n".join(l for l in lines if l)


@app.post("/api/ai/match-jd", response_model=schemas.JDMatchResponse)
def ai_match_jd(request: schemas.JDMatchRequest, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = _resume_to_plain_text(resume)
    result = analyze_against_jd(resume_text, request.job_description)
    return schemas.JDMatchResponse(**result)


@app.get("/api/status")
def api_status():
    return {"status": "CloudFolio API is running"}


@app.get("/api/ai/status")
def ai_status():
    """Diagnostic only — confirms whether the backend process sees an API
    key, without ever revealing it. Useful when the AI button silently
    no-ops and you need to know whether it's an env-var problem or
    something else."""
    from ai_suggestions import GEMINI_API_KEY
    key_present = bool(GEMINI_API_KEY)
    return {
        "gemini_key_detected": key_present,
        "key_length": len(GEMINI_API_KEY) if key_present else 0,
    }


# Serve the frontend (index.html, app.js, style.css) from the same process,
# so you only need one terminal / one command to run the whole app.
# The frontend lives at ../frontend relative to this file.
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
