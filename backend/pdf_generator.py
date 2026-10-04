"""
Generates an ATS-friendly PDF resume from resume data.
Single clean template: left-aligned, no tables/columns/graphics —
this is deliberate, since ATS parsers choke on multi-column layouts.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib import colors
import io


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NameHeader", fontSize=20, leading=24, spaceAfter=2,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="ContactLine", fontSize=9.5, leading=12,
        textColor=colors.HexColor("#444444"), spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=12, leading=14, spaceBefore=12,
        spaceAfter=4, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=10, leading=13.5, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="ItemTitle", fontSize=10.5, leading=13,
        fontName="Helvetica-Bold", spaceBefore=4,
    ))
    styles.add(ParagraphStyle(
        name="ItemMeta", fontSize=9.5, leading=12,
        textColor=colors.HexColor("#555555"),
    ))
    return styles


def generate_resume_pdf(resume_data: dict) -> bytes:
    """
    resume_data matches the ResumeOut/Resume shape (dict form).
    Returns raw PDF bytes — caller decides whether to save to disk,
    upload to S3, or stream straight back in an HTTP response.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )
    styles = _build_styles()
    story = []

    # --- Header ---
    story.append(Paragraph(resume_data.get("full_name", ""), styles["NameHeader"]))

    contact_bits = [
        resume_data.get("email"),
        resume_data.get("phone"),
        resume_data.get("location"),
        resume_data.get("linkedin"),
        resume_data.get("github"),
    ]
    contact_line = "  |  ".join([c for c in contact_bits if c])
    story.append(Paragraph(contact_line, styles["ContactLine"]))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc")))

    # --- Summary ---
    if resume_data.get("summary"):
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles["SectionHeading"]))
        story.append(Paragraph(resume_data["summary"], styles["Body"]))

    # --- Skills ---
    skills = resume_data.get("skills") or []
    if skills:
        story.append(Paragraph("SKILLS", styles["SectionHeading"]))
        story.append(Paragraph(" &nbsp;•&nbsp; ".join(skills), styles["Body"]))

    # --- Experience ---
    experience = resume_data.get("experience") or []
    if experience:
        story.append(Paragraph("EXPERIENCE", styles["SectionHeading"]))
        for item in experience:
            title = item.get("title", "")
            company = item.get("company", "")
            duration = item.get("duration", "")
            story.append(Paragraph(f"{title} — {company}", styles["ItemTitle"]))
            if duration:
                story.append(Paragraph(duration, styles["ItemMeta"]))
            if item.get("description"):
                story.append(Paragraph(item["description"], styles["Body"]))

    # --- Projects ---
    projects = resume_data.get("projects") or []
    if projects:
        story.append(Paragraph("PROJECTS", styles["SectionHeading"]))
        for item in projects:
            title = item.get("title", "")
            link = item.get("link", "")
            header = f"{title} ({link})" if link else title
            story.append(Paragraph(header, styles["ItemTitle"]))
            if item.get("description"):
                story.append(Paragraph(item["description"], styles["Body"]))

    # --- Education ---
    education = resume_data.get("education") or []
    if education:
        story.append(Paragraph("EDUCATION", styles["SectionHeading"]))
        for item in education:
            degree = item.get("degree", "")
            institution = item.get("institution", "")
            duration = item.get("duration", "")
            story.append(Paragraph(f"{degree} — {institution}", styles["ItemTitle"]))
            if duration:
                story.append(Paragraph(duration, styles["ItemMeta"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
