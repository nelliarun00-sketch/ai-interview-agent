"""
Resume Intelligence & ATS Screening Service
-------------------------------------------
Parses PDF, DOCX, or text in memory, evaluates ATS compatibility score,
extracts skills, flags missing keywords, and generates project interview questions.
"""

import io
import os
from typing import Dict, Any, Tuple
from core.models import StudentState
from core.repositories.session_repo import data_repo
from ai.client import ai_client
from ai.validator import parse_and_validate
from ai.schemas import RESUME_ANALYSIS_SCHEMA
from ai.trace import ai_trace


def extract_text_from_file(file_storage) -> str:
    """Extracts text from uploaded PDF, DOCX, or TXT file stream in memory."""
    filename = file_storage.filename.lower()
    stream = io.BytesIO(file_storage.read())

    if filename.endswith(".pdf"):
        import pypdf
        reader = pypdf.PdfReader(stream)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip()
    elif filename.endswith(".docx"):
        import docx
        doc = docx.Document(stream)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    else:
        # Plain text
        return stream.read().decode("utf-8", errors="ignore").strip()


def analyze_resume(resume_text: str, student: StudentState) -> Dict[str, Any]:
    """
    Evaluates resume against student target career using Gemini AI.
    """
    career = student.goal.career_title
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai", "prompts", "resume_eval.v1.txt"
    )
    template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

    rendered = template.format(
        career=career,
        resume_text=resume_text[:4000] # Safe cap
    )

    def fallback_resume_eval():
        return {
            "ats_score": 75,
            "sections_present": ["Education", "Skills", "Projects", "Experience"],
            "skills_extracted": ["Python", "SQL", "Git", "Data Structures"],
            "quantified_bullets_found": 2,
            "weak_bullets_with_rewrites": [
                {
                    "original": "Worked on web application using Python.",
                    "critique": "Lacks specific engineering actions and measurable business impact.",
                    "improved": "Developed REST APIs using Python & Flask, reducing endpoint latency by 25% across 5,000 requests."
                }
            ],
            "missing_skills": ["Docker", "Unit Testing", "System Design"],
            "suggested_interview_questions": [
                "Can you walk through the system architecture of your top listed project?",
                "What was the most challenging technical bug you encountered in your project and how did you resolve it?",
                "How did you evaluate performance trade-offs in your database design?",
                "If you had to scale your application 10x, what components would you refactor?"
            ],
            "summary": f"Strong foundational resume for entry-level {career}. Adding quantified metrics and deployment tools will elevate ATS ranking."
        }

    raw_text, latency, err = ai_client.generate(rendered, json_mode=True)
    validated, source, val_err = parse_and_validate(raw_text, RESUME_ANALYSIS_SCHEMA, fallback_resume_eval)

    # Store analysis on student state
    student.resume_analysis = validated

    ai_trace.record(
        operation="analyze_resume",
        prompt_version="resume_eval.v1",
        inputs={"career": career, "char_len": len(resume_text)},
        raw_output=raw_text or "",
        validated_output=validated,
        latency_ms=latency,
        source=source,
        error=err or val_err
    )

    return validated
