from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)


from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.matching_engine import calculate_match_score, rank_jobs
from app.models import JobPosting
from app.pdf_processor import MAX_PDF_SIZE, extract_text_from_pdf
from app.schemas import JobCreate, JobResponse
from app.skills_analyzer import analyze_skill_gap


app = FastAPI(
    title="AI Job Matching API",
    description=(
        "An AI-powered job matching application "
        "built with Python, FastAPI, and PostgreSQL."
    ),
    version="1.1.0",
)


# -----------------------------
# Request and Response Models
# -----------------------------

class MatchRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    job_description: str = Field(min_length=1)

class SavedJobsRankRequest(BaseModel):
    resume_text: str = Field(min_length=1) 

class SavedJobsRankRequest(BaseModel):
    resume_text: str = Field(min_length=1)

class MatchResponse(BaseModel):
    match_score: float
    interpretation: str
    resume_skills: list[str]
    job_skills: list[str]
    matching_skills: list[str]
    missing_skills: list[str]
    skill_coverage: float


class JobToRank(BaseModel):
    id: int
    title: str
    company: str
    description: str = Field(min_length=1)


class RankJobsRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    jobs: list[JobToRank] = Field(min_length=1)


class RankedJob(JobToRank):
    match_score: float


class RankJobsResponse(BaseModel):
    ranked_jobs: list[RankedJob]


class ResumeUploadResponse(BaseModel):
    filename: str
    extracted_text: str
    character_count: int
    detected_skills: list[str]


# -----------------------------
# Basic API Endpoints
# -----------------------------

@app.get("/")
def root():
    return {
        "application": "AI Job Matching API",
        "version": "1.1.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# -----------------------------
# PostgreSQL Job Endpoints
# -----------------------------

@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=201,
)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
):
    new_job = JobPosting(
        title=job.title,
        company=job.company,
        location=job.location,
        remote=job.remote,
        description=job.description,
    )

    db.add(new_job)

    try:
        db.commit()
        db.refresh(new_job)
    except Exception:
        db.rollback()
        raise

    return new_job


@app.get(
    "/jobs",
    response_model=list[JobResponse],
)
def get_jobs(
    keyword: str | None = None,
    location: str | None = None,
    remote: bool | None = None,
    db: Session = Depends(get_db),
):
    statement = select(JobPosting)

    if keyword:
        search_term = f"%{keyword}%"

        statement = statement.where(
            JobPosting.title.ilike(search_term)
            | JobPosting.description.ilike(search_term)
        )

    if location:
        statement = statement.where(
            JobPosting.location.ilike(f"%{location}%")
        )

    if remote is not None:
        statement = statement.where(
            JobPosting.remote == remote
        )

    statement = statement.order_by(JobPosting.id)

    return db.scalars(statement).all()



@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(JobPosting, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    return job


# -----------------------------
# AI Resume Matching Endpoint
# -----------------------------

@app.post(
    "/match",
    response_model=MatchResponse,
)
def match_resume_to_job(request: MatchRequest):
    score = calculate_match_score(
        request.resume_text,
        request.job_description,
    )

    if score >= 75:
        interpretation = "High semantic similarity"
    elif score >= 50:
        interpretation = "Moderate semantic similarity"
    else:
        interpretation = "Low semantic similarity"

    skills = analyze_skill_gap(
        request.resume_text,
        request.job_description,
    )

    return MatchResponse(
        match_score=score,
        interpretation=interpretation,
        **skills,
    )


# -----------------------------
# AI Job Ranking Endpoint
# -----------------------------

@app.post(
    "/rank-jobs",
    response_model=RankJobsResponse,
)
def rank_job_matches(request: RankJobsRequest):
    jobs = [
        job.model_dump()
        for job in request.jobs
    ]

    results = rank_jobs(
        resume_text=request.resume_text,
        jobs=jobs,
    )

    return RankJobsResponse(
        ranked_jobs=results,
    )


# -----------------------------
# PDF Resume Upload Endpoint
# -----------------------------

@app.post(
    "/upload-resume",
    response_model=ResumeUploadResponse,
)
async def upload_resume(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read(MAX_PDF_SIZE + 1)
    await file.close()

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF file exceeds the 10 MB limit.",
        )

    try:
        extracted_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    detected_skills = analyze_skill_gap(
        extracted_text,
        "",
    )["resume_skills"]

    return ResumeUploadResponse(
        filename=file.filename or "resume.pdf",
        extracted_text=extracted_text,
        character_count=len(extracted_text),
        detected_skills=detected_skills,
    )



# -----------------------------
# Database-Powered AI Job Ranking
# -----------------------------

@app.post(
    "/rank-saved-jobs",
    response_model=RankJobsResponse,
)
def rank_saved_jobs(
    request: SavedJobsRankRequest,
    db: Session = Depends(get_db),
):
    """
    Retrieve saved jobs from PostgreSQL and rank
    them by semantic similarity to a resume.
    """
    statement = select(JobPosting).order_by(JobPosting.id)

    saved_jobs = db.scalars(statement).all()

    if not saved_jobs:
        return RankJobsResponse(ranked_jobs=[])

    jobs = [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
        }
        for job in saved_jobs
    ]

    ranked_results = rank_jobs(
        resume_text=request.resume_text,
        jobs=jobs,
    )

    return RankJobsResponse(
        ranked_jobs=ranked_results,
    )


# ----------------------------------
# Delete Job from PostgreSQL
# ----------------------------------

from fastapi import HTTPException


@app.delete("/jobs/{job_id}", tags=["Jobs"])
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a saved job posting by its database ID.
    """

    job = db.get(JobPosting, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found",
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Job deleted successfully",
        "deleted_job_id": job_id,
    }
