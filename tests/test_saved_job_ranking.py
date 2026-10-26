
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


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
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_job(client, title, description):
    response = client.post(
        "/jobs",
        json={
            "title": title,
            "company": "Example Company",
            "location": "Remote",
            "remote": True,
            "description": description,
        },
    )

    assert response.status_code == 201
    return response.json()


def test_rank_saved_jobs_empty_database(client):
    response = client.post(
        "/rank-saved-jobs",
        json={"resume_text": "Python developer"},
    )

    assert response.status_code == 200
    assert response.json() == {"ranked_jobs": []}


def test_rank_saved_jobs(client):
    python_job = create_job(
        client,
        "Python Developer",
        "Build Python FastAPI applications.",
    )

    data_job = create_job(
        client,
        "Data Engineer",
        "Build SQL data pipelines.",
    )

    mock_results = [
        {
            "id": python_job["id"],
            "title": "Python Developer",
            "company": "Example Company",
            "description": "Build Python FastAPI applications.",
            "match_score": 90.0,
        },
        {
            "id": data_job["id"],
            "title": "Data Engineer",
            "company": "Example Company",
            "description": "Build SQL data pipelines.",
            "match_score": 45.0,
        },
    ]

    with patch(
        "app.main.rank_jobs",
        return_value=mock_results,
    ) as mock_rank:
        response = client.post(
            "/rank-saved-jobs",
            json={"resume_text": "Python FastAPI developer"},
        )

    assert response.status_code == 200

    results = response.json()["ranked_jobs"]
    assert len(results) == 2
    assert results[0]["match_score"] == 90.0
    assert results[1]["match_score"] == 45.0

    mock_rank.assert_called_once()

    call_kwargs = mock_rank.call_args.kwargs
    assert call_kwargs["resume_text"] == "Python FastAPI developer"
    assert len(call_kwargs["jobs"]) == 2


def test_rank_saved_jobs_rejects_empty_resume(client):
    response = client.post(
        "/rank-saved-jobs",
        json={"resume_text": ""},
    )

    assert response.status_code == 422
