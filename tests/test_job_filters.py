
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import JobPosting


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            jobs = [
                {
                    "title": "Python Backend Developer",
                    "company": "Example Tech",
                    "location": "Remote",
                    "remote": True,
                    "description": "Build APIs using Python and FastAPI.",
                },
                {
                    "title": "Machine Learning Engineer",
                    "company": "Example AI",
                    "location": "San Francisco, CA",
                    "remote": False,
                    "description": "Develop machine learning pipelines.",
                },
                {
                    "title": "Remote Data Engineer",
                    "company": "Example Data",
                    "location": "Remote",
                    "remote": True,
                    "description": "Build SQL data pipelines.",
                },
            ]

            for job in jobs:
                response = test_client.post("/jobs", json=job)
                assert response.status_code == 201

            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_filter_by_keyword(client):
    response = client.get("/jobs?keyword=python")

    assert response.status_code == 200
    jobs = response.json()

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Backend Developer"


def test_filter_by_remote(client):
    response = client.get("/jobs?remote=true")

    assert response.status_code == 200
    jobs = response.json()

    assert len(jobs) == 2
    assert all(job["remote"] for job in jobs)


def test_filter_by_location(client):
    response = client.get("/jobs?location=San%20Francisco")

    assert response.status_code == 200
    jobs = response.json()

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Machine Learning Engineer"


def test_filter_by_keyword_and_remote(client):
    response = client.get(
        "/jobs?keyword=python&remote=true"
    )

    assert response.status_code == 200
    jobs = response.json()

    assert len(jobs) == 1
    assert jobs[0]["remote"] is True


def test_filter_no_matches(client):
    response = client.get("/jobs?keyword=accountant")

    assert response.status_code == 200
    assert response.json() == []


def test_filter_case_insensitive(client):
    response = client.get("/jobs?keyword=PYTHON")

    assert response.status_code == 200
    assert len(response.json()) == 1
