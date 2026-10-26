
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_match_endpoint():
    with patch(
        "app.main.calculate_match_score",
        return_value=82.5,
    ):
        response = client.post(
            "/match",
            json={
                "resume_text": "Python FastAPI Docker",
                "job_description": "Python FastAPI AWS",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["match_score"] == 82.5
    assert data["interpretation"] == "High semantic similarity"
    assert data["matching_skills"] == ["fastapi", "python"]
    assert data["missing_skills"] == ["aws"]
    assert data["skill_coverage"] == 66.67


def test_match_moderate_similarity():
    with patch(
        "app.main.calculate_match_score",
        return_value=62.0,
    ):
        response = client.post(
            "/match",
            json={
                "resume_text": "Python developer",
                "job_description": "Software engineer",
            },
        )

    assert response.status_code == 200
    assert response.json()["interpretation"] == (
        "Moderate semantic similarity"
    )


def test_match_low_similarity():
    with patch(
        "app.main.calculate_match_score",
        return_value=25.0,
    ):
        response = client.post(
            "/match",
            json={
                "resume_text": "Python developer",
                "job_description": "Marketing specialist",
            },
        )

    assert response.status_code == 200
    assert response.json()["interpretation"] == (
        "Low semantic similarity"
    )


def test_match_rejects_empty_resume():
    response = client.post(
        "/match",
        json={
            "resume_text": "",
            "job_description": "Python developer",
        },
    )

    assert response.status_code == 422


def test_rank_jobs_endpoint():
    mock_results = [
        {
            "id": 1,
            "title": "Python Developer",
            "company": "Example Tech",
            "description": "Python FastAPI Docker",
            "match_score": 90.0,
        },
        {
            "id": 2,
            "title": "Marketing Specialist",
            "company": "Example Marketing",
            "description": "Social media marketing",
            "match_score": 20.0,
        },
    ]

    with patch(
        "app.main.rank_jobs",
        return_value=mock_results,
    ):
        response = client.post(
            "/rank-jobs",
            json={
                "resume_text": "Python FastAPI Docker",
                "jobs": [
                    {
                        "id": 1,
                        "title": "Python Developer",
                        "company": "Example Tech",
                        "description": "Python FastAPI Docker",
                    },
                    {
                        "id": 2,
                        "title": "Marketing Specialist",
                        "company": "Example Marketing",
                        "description": "Social media marketing",
                    },
                ],
            },
        )

    assert response.status_code == 200

    ranked_jobs = response.json()["ranked_jobs"]

    assert len(ranked_jobs) == 2
    assert ranked_jobs[0]["match_score"] == 90.0
    assert ranked_jobs[1]["match_score"] == 20.0


def test_rank_jobs_rejects_empty_list():
    response = client.post(
        "/rank-jobs",
        json={
            "resume_text": "Python developer",
            "jobs": [],
        },
    )

    assert response.status_code == 422
