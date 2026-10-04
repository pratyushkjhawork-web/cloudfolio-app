"""
AI-powered suggestion feature — the "AI-Based Application" element of
the project. Kept to ONE feature (improve a summary/experience bullet)
rather than four, per the scoped-down plan.

Uses Gemini (via the current `google-genai` SDK) by default. Swap to
OpenAI by uncommenting the alternate block at the bottom — the
function signature (suggest_improvement) stays identical either way,
so nothing else in the app needs to change.
"""

import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

# Loads variables from a .env file (in the backend/ folder) into the
# process environment, if that file exists. Safe to call even if the
# file is missing — it just does nothing in that case.
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Tried in order. If the first is overloaded (503) after retries, we fall
# back to the next one rather than failing the whole request.
_MODEL_CANDIDATES = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
_MODEL_NAME = _MODEL_CANDIDATES[0]  # kept for backward compatibility elsewhere


def _generate_with_retry(prompt: str, max_retries: int = 2, backoff_seconds: float = 2.0):
    """
    Calls Gemini with automatic retry-on-503 (server overload) and
    fallback across _MODEL_CANDIDATES. Raises the last error if every
    model/retry combination fails, so callers can still show a clear
    message rather than the app silently hanging.
    """
    last_error = None
    for model_name in _MODEL_CANDIDATES:
        for attempt in range(max_retries + 1):
            try:
                return _client.models.generate_content(model=model_name, contents=prompt)
            except genai_errors.ServerError as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(backoff_seconds * (attempt + 1))  # 2s, then 4s
                # else: give up on this model, try the next candidate
            except genai_errors.ClientError as e:
                # Not a traffic/overload issue (e.g. bad model name, bad
                # request) — retrying won't help, try the next model.
                last_error = e
                break
    raise last_error

_PROMPT_TEMPLATES = {
    "summary": (
        "You are a professional resume writer. Rewrite the following "
        "professional summary to be more concise, impactful, and ATS-friendly. "
        "Keep it truthful — do not invent skills, tools, or achievements that "
        "are not implied by the original text. Return ONLY the rewritten "
        "summary, no preamble, no quotation marks.\n\n"
        "Original summary:\n{text}"
    ),
    "experience": (
        "You are a professional resume writer. Rewrite the following "
        "work experience bullet point to be more results-oriented and "
        "ATS-friendly. Keep it truthful — do not invent metrics, numbers, "
        "or outcomes that are not implied by the original text. Return ONLY "
        "the rewritten bullet point, no preamble, no quotation marks.\n\n"
        "Original text:\n{text}"
    ),
}


import json


def analyze_against_jd(resume_text: str, job_description: str) -> dict:
    """
    Compares a resume against a job description and returns a match
    score + keyword gaps + improvement suggestions. Returns a plain
    dict matching schemas.JDMatchResponse's fields.

    Graceful no-key fallback: returns a zeroed/neutral response with a
    suggestion that explains no key is configured, rather than crashing.
    """
    if not _client:
        return {
            "match_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": ["AI analysis unavailable — GEMINI_API_KEY is not configured on the backend."],
        }

    prompt = (
        "You are an ATS (Applicant Tracking System) and resume-screening expert. "
        "Compare the RESUME below against the JOB DESCRIPTION below. "
        "Be honest and strict — do not inflate the score. Base your analysis "
        "ONLY on what is actually written in the resume; do not assume skills "
        "or experience that are not stated.\n\n"
        "Respond with ONLY a valid JSON object (no markdown fences, no preamble), "
        "matching exactly this shape:\n"
        "{\n"
        '  "match_score": <integer 0-100>,\n'
        '  "matched_keywords": [<strings — skills/terms from the JD that ARE present in the resume>],\n'
        '  "missing_keywords": [<strings — important skills/terms from the JD that are NOT present in the resume>],\n'
        '  "suggestions": [<strings — 3 to 5 concrete, actionable suggestions to improve the match>]\n'
        "}\n\n"
        f"RESUME:\n{resume_text}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )

    try:
        response = _generate_with_retry(prompt)
    except Exception:
        return {
            "match_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": ["AI analysis temporarily unavailable — Gemini is experiencing high traffic. Please try again in a minute."],
        }

    raw = response.text.strip()
    # Models sometimes wrap JSON in ```json fences despite instructions — strip if present.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fail safe rather than crashing the request — surface the raw
        # text as a single suggestion so it's at least visible/debuggable.
        return {
            "match_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": [f"Could not parse AI response as JSON. Raw response: {raw[:300]}"],
        }

    return {
        "match_score": int(parsed.get("match_score", 0)),
        "matched_keywords": parsed.get("matched_keywords", []),
        "missing_keywords": parsed.get("missing_keywords", []),
        "suggestions": parsed.get("suggestions", []),
    }


def suggest_improvement(text: str, field_type: str = "summary") -> str:
    """
    Returns an AI-improved version of `text`. Falls back to returning
    the original text unchanged if no API key is configured, so the
    rest of the app still works (and doesn't crash) without an API key
    set — useful during early local dev before you've got a key.
    """
    if not _client:
        return text  # graceful no-op, not a crash

    template = _PROMPT_TEMPLATES.get(field_type, _PROMPT_TEMPLATES["summary"])
    prompt = template.format(text=text)

    try:
        response = _generate_with_retry(prompt)
        return response.text.strip()
    except Exception:
        # All models/retries exhausted (e.g. sustained high traffic on
        # Google's side). Fail soft — return the original text rather
        # than a 500 error, so the UI can show "no change" instead of crashing.
        return text


# --- OpenAI alternative (uncomment to use instead of Gemini) ---
#
# from openai import OpenAI
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
# _client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
#
# def suggest_improvement(text: str, field_type: str = "summary") -> str:
#     if not _client:
#         return text
#     template = _PROMPT_TEMPLATES.get(field_type, _PROMPT_TEMPLATES["summary"])
#     prompt = template.format(text=text)
#     completion = _client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}],
#     )
#     return completion.choices[0].message.content.strip()
