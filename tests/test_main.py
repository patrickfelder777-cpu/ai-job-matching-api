
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import JobPosting


# Temporary in-memory database for testing
test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["application"] == "AI Job Matching API"
    assert data["version"] == "1.1.0"
    assert data["status"] == "running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_jobs_empty(client):
    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json() == []


def test_create_job(client):
    response = client.post(
        "/jobs",
        json={
            "title": "Junior Python Developer",
            "company": "Example Tech",
            "location": "Remote",
            "remote": True,
            "description": "Build Python APIs using FastAPI.",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Junior Python Developer"
    assert data["company"] == "Example Tech"
    assert data["remote"] is True


def test_get_jobs_after_creation(client):
    client.post(
        "/jobs",
        json={
            "title": "Machine Learning Engineer",
            "company": "Sample AI",
            "location": "San Francisco, CA",
            "remote": False,
            "description": "Develop machine learning models.",
        },
    )

    response = client.get("/jobs")

    assert response.status_code == 200

    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Machine Learning Engineer"


def test_get_job_by_id(client):
    create_response = client.post(
        "/jobs",
        json={
            "title": "AI Application Developer",
            "company": "Demo Software",
            "location": "Remote",
            "remote": True,
            "description": "Build AI-powered applications.",
        },
    )

    job_id = create_response.json()["id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "AI Application Developer"


def test_get_nonexistent_job(client):
    response = client.get("/jobs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."


def test_create_job_missing_title(client):
    response = client.post(
        "/jobs",
        json={
            "company": "Example Tech",
            "location": "Remote",
            "remote": True,
            "description": "Build Python applications.",
        },
    )

    assert response.status_code == 422
