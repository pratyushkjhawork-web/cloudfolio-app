"""
Data model. Kept intentionally flat (one table) for speed —
JSON columns hold list-shaped data (skills, experience, projects)
instead of separate related tables. Good enough for a single-user,
no-auth MVP; normalize later only if you actually have time.
"""

from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)

    # Content
    summary = Column(String, nullable=True)  # professional summary — AI can help improve this
    skills = Column(JSON, nullable=True)       # list[str]
    experience = Column(JSON, nullable=True)   # list[{title, company, duration, description}]
    education = Column(JSON, nullable=True)    # list[{degree, institution, duration}]
    projects = Column(JSON, nullable=True)     # list[{title, description, link}]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
