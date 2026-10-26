
import re


TECHNICAL_SKILLS = {
    "python": ["python"],
    "sql": ["sql"],
    "fastapi": ["fastapi", "fast api"],
    "flask": ["flask"],
    "django": ["django"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud platform"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb"],
    "git": ["git"],
    "github actions": ["github actions"],
    "ci/cd": ["ci/cd", "continuous integration"],
    "pytest": ["pytest"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "machine learning": ["machine learning"],
    "deep learning": ["deep learning"],
    "nlp": ["nlp", "natural language processing"],
    "llm": ["llm", "large language model"],
    "rag": ["rag", "retrieval augmented generation"],
    "streamlit": ["streamlit"],
    "rest api": ["rest api", "restful api", "rest apis"],
}


def extract_skills(text: str) -> list[str]:
    """
    Extract recognized technical skills from text.

    Uses word boundaries to reduce partial-word matches.
    """
    if not text or not text.strip():
        return []

    text = text.lower()
    found_skills = set()

    for skill, aliases in TECHNICAL_SKILLS.items():
        for alias in aliases:
            pattern = (
                r"(?<!\w)"
                + re.escape(alias)
                + r"(?!\w)"
            )

            if re.search(pattern, text):
                found_skills.add(skill)
                break

    return sorted(found_skills)


def analyze_skill_gap(
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Compare skills explicitly mentioned in the resume
    and job description.
    """
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_description))

    matching_skills = sorted(resume_skills & job_skills)
    missing_skills = sorted(job_skills - resume_skills)

    coverage = (
        round(
            len(matching_skills) / len(job_skills) * 100,
            2,
        )
        if job_skills
        else 0.0
    )

    return {
        "resume_skills": sorted(resume_skills),
        "job_skills": sorted(job_skills),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "skill_coverage": coverage,
    }
