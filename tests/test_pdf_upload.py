
from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.pdf_processor import MAX_PDF_SIZE


client = TestClient(app)


def create_test_pdf(text: str) -> bytes:
    """Create a small PDF in memory for testing."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)

    pdf_bytes = document.tobytes()
    document.close()

    return pdf_bytes


def test_upload_valid_pdf():
    pdf_bytes = create_test_pdf(
        "Python developer with FastAPI and Docker experience."
    )

    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "resume.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "resume.pdf"
    assert "Python developer" in data["extracted_text"]
    assert data["character_count"] > 0
    assert "python" in data["detected_skills"]
    assert "fastapi" in data["detected_skills"]
    assert "docker" in data["detected_skills"]


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "resume.txt",
                BytesIO(b"This is not a PDF."),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF files are supported."
    )


def test_upload_rejects_invalid_pdf():
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "resume.pdf",
                BytesIO(b"Not a real PDF file"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400


def test_upload_rejects_oversized_pdf():
    oversized_data = (
        b"%PDF-1.7\n"
        + b"x" * (MAX_PDF_SIZE + 1)
    )

    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "large_resume.pdf",
                BytesIO(oversized_data),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413


def test_upload_rejects_pdf_without_text():
    document = fitz.open()
    document.new_page()

    pdf_bytes = document.tobytes()
    document.close()

    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "empty_resume.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "No readable text" in response.json()["detail"]
