"""
Pydantic schemas — define the shape of data going in/out of the API.
Kept loose (most fields optional) since a resume can be built up
incrementally and you don't want validation errors blocking a save.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    description: str


class EducationItem(BaseModel):
    degree: str
    institution: str
    duration: str


class ProjectItem(BaseModel):
    title: str
    description: str
    link: Optional[str] = None


class ResumeBase(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = []
    experience: Optional[List[ExperienceItem]] = []
    education: Optional[List[EducationItem]] = []
    projects: Optional[List[ProjectItem]] = []


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(ResumeBase):
    pass


class ResumeOut(ResumeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AISuggestRequest(BaseModel):
    text: str
    field_type: str = "summary"  # "summary" or "experience"


class AISuggestResponse(BaseModel):
    original: str
    suggestion: str


class JDMatchRequest(BaseModel):
    resume_id: int
    job_description: str


class JDMatchResponse(BaseModel):
    match_score: int  # 0-100
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
