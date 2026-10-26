
# AI Job Matching Assistant

An AI-powered career matching application that analyzes PDF resumes, identifies technical skills, and ranks job opportunities using semantic similarity.

## Features

- PDF resume upload and text extraction
- Automatic technical skill detection
- AI-powered resume-to-job matching
- Job ranking using sentence-transformer embeddings
- Matching and missing skill analysis
- Job search and filtering
- Interactive Streamlit dashboard
- REST API built with FastAPI
- PostgreSQL database for saved job postings
- Docker Compose deployment

## Technology Stack

- Python 3.11
- FastAPI
- Streamlit
- PostgreSQL
- SQLAlchemy
- Sentence Transformers
- Scikit-learn
- PyMuPDF
- Docker and Docker Compose
- Pytest

## How It Works

1. Upload a PDF resume.
2. The application extracts the resume text.
3. Technical skills are identified.
4. Sentence-transformer embeddings measure semantic similarity between the resume and saved job descriptions.
5. Jobs are ranked by similarity score.
6. Skill-gap analysis identifies matching and missing technical skills.

Similarity scores represent text alignment, not the probability of being hired.

## Run Locally with Docker

Clone the repository:

```bash
git clone https://github.com/patrickfelder777-cpu/ai-job-matching-api.git
cd ai-job-matching-api
```

Create a `.env` file containing your PostgreSQL connection configuration.

Start the application:

```bash
docker compose up --build -d
```

Access the application:

- Streamlit dashboard: http://localhost:8504
- FastAPI documentation: http://localhost:8001/docs

## Testing

Run automated tests:

```bash
python -m pytest -v
```

## Project Status

Working portfolio application with Docker deployment, resume analysis, semantic job matching, and PostgreSQL persistence.

Job postings currently use demonstration data rather than a live job-search provider.


## 🎥 Project Demo

Watch a narrated demonstration of the AI Job Matching Assistant, including:

- PDF resume upload and technical skill extraction
- AI-powered job recommendations
- Semantic similarity scoring
- Interactive job ranking dashboard
- Technical skill-gap analysis

[▶ Watch the AI Job Matching Assistant Demo](demo/ai_job_matching_demo.mp4)


## Author

Patrick Felder

GitHub: https://github.com/patrickfelder777-cpu
