
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_model():
    """
    Load the sentence-transformer model once and reuse it.
    """
    return SentenceTransformer(MODEL_NAME)


def calculate_match_score(resume_text: str, job_description: str) -> float:
    """
    Calculate semantic similarity between a resume and job description.

    Returns a score from 0.0 to 100.0.
    Higher scores indicate stronger semantic similarity.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    model = load_model()

    embeddings = model.encode(
        [resume_text, job_description],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    similarity = cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1),
    )[0][0]

    score = max(0.0, min(100.0, float(similarity) * 100))

    return round(score, 2)


def rank_jobs(resume_text: str, jobs: list[dict]) -> list[dict]:
    """
    Rank job descriptions by semantic similarity to the resume.

    Each job must include a 'description' field.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    ranked_jobs = []

    for job in jobs:
        if "description" not in job:
            raise ValueError("Each job must contain a description.")

        score = calculate_match_score(
            resume_text,
            job["description"],
        )

        ranked_jobs.append({
            **job,
            "match_score": score,
        })

    return sorted(
        ranked_jobs,
        key=lambda job: job["match_score"],
        reverse=True,
    )
