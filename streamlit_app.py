
import os

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

st.set_page_config(
    page_title="AI Job Matching Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------
# Custom Dashboard Styling
# ----------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B1220;
        color: #F1F5F9;
    }

    [data-testid="stSidebar"] {
        background-color: #111C2E;
        border-right: 1px solid #26354B;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #F8FAFC;
        letter-spacing: -0.4px;
    }

    .dashboard-hero {
        padding: 28px 32px;
        border: 1px solid #273B57;
        border-radius: 16px;
        background: linear-gradient(
            120deg,
            #142642,
            #101B30
        );
        margin-bottom: 24px;
    }

    .dashboard-title {
        font-size: 36px;
        font-weight: 750;
        color: #FFFFFF;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        font-size: 16px;
        color: #B8C7DD;
        line-height: 1.6;
    }

    .section-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #60A5FA;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .skill-tag {
        display: inline-block;
        padding: 6px 11px;
        margin: 4px 5px 4px 0;
        border-radius: 20px;
        background-color: #193B36;
        border: 1px solid #286D5B;
        color: #9EF0CE;
        font-size: 13px;
        font-weight: 500;
    }

    .missing-tag {
        display: inline-block;
        padding: 6px 11px;
        margin: 4px 5px 4px 0;
        border-radius: 20px;
        background-color: #45252A;
        border: 1px solid #8C4149;
        color: #FFB4B4;
        font-size: 13px;
        font-weight: 500;
    }

    .rank-label {
        font-size: 12px;
        font-weight: 700;
        color: #93C5FD;
        letter-spacing: 1px;
    }

    .job-company {
        font-size: 14px;
        color: #A9BDD7;
    }

    .small-note {
        color: #94A3B8;
        font-size: 13px;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563EB;
        border-color: #2563EB;
        color: white;
        border-radius: 9px;
        font-weight: 600;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
    }

    div[data-testid="stMetric"] {
        background-color: #142238;
        border: 1px solid #293A52;
        border-radius: 12px;
        padding: 16px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------
# API Helpers
# ----------------------------------

def api_request(method, endpoint, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_URL}{endpoint}",
            timeout=120,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        st.error(f"API error: {error}")
        return None

    except ValueError:
        st.error("The API returned an invalid JSON response.")
        return None


def display_skill_tags(skills, missing=False):
    if not skills:
        st.caption("None detected.")
        return

    css_class = "missing-tag" if missing else "skill-tag"

    import html

    tags = "".join(
        f'<span class="{css_class}">'
        f'{html.escape(str(skill))}'
        "</span>"
        for skill in skills
    )

    st.markdown(tags, unsafe_allow_html=True)


def normalize_score(value):
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def similarity_label(score):
    if score >= 75:
        return "Strong semantic alignment"
    if score >= 50:
        return "Moderate semantic alignment"
    return "Limited semantic alignment"


# ----------------------------------
# Session State
# ----------------------------------

defaults = {
    "resume_text": "",
    "resume_skills": [],
    "ranked_jobs": [],
    "search_results": None,
    "skill_gap_results": {},
    "ranking_completed": False,
}

for key, default_value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# ----------------------------------
# Sidebar
# ----------------------------------

with st.sidebar:
    st.title("💼 JobMatch AI")
    st.caption("AI-powered career matching platform")

    st.divider()

    st.subheader("Application Status")

    if st.button(
        "Check API Connection",
        use_container_width=True,
    ):
        result = api_request("GET", "/health")

        if result and result.get("status") == "healthy":
            st.success("Backend connected!")
        else:
            st.error("Backend connection unavailable.")

    st.caption(f"API: {API_URL}")

    st.divider()

    st.subheader("Resume Status")

    if st.session_state.resume_text:
        st.success("Resume analyzed")
        st.metric(
            "Skills Detected",
            len(st.session_state.resume_skills),
        )
    else:
        st.info("No resume uploaded yet.")

    st.divider()

    st.caption(
        "Python · FastAPI · PostgreSQL · "
        "Sentence Transformers · Streamlit"
    )


# ----------------------------------
# Hero Section
# ----------------------------------

st.markdown(
    """
    <div class="dashboard-hero">
        <div class="section-label">
            Intelligent Career Discovery
        </div>
        <div class="dashboard-title">
            AI Job Matching Assistant
        </div>
        <div class="dashboard-subtitle">
            Upload your resume, explore opportunities,
            compare semantic similarity, and identify
            technical skill gaps using AI.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


resume_tab, jobs_tab, matches_tab = st.tabs(
    [
        "📄 Resume Analysis",
        "🔎 Job Explorer",
        "🎯 AI Job Matches",
    ]
)


# ----------------------------------
# Resume Analysis
# ----------------------------------

with resume_tab:
    st.header("Resume Intelligence")

    st.write(
        "Upload your PDF resume to extract text "
        "and identify technical skills."
    )

    uploaded_file = st.file_uploader(
        "Choose your PDF resume",
        type=["pdf"],
        help="Maximum file size: 10 MB.",
    )

    if uploaded_file is not None:
        if st.button(
            "Analyze Resume",
            type="primary",
            use_container_width=False,
        ):
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("PDF must be 10 MB or smaller.")
            else:
                with st.spinner("Analyzing your resume..."):
                    result = api_request(
                        "POST",
                        "/upload-resume",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                "application/pdf",
                            )
                        },
                    )

                if result is not None:
                    st.session_state.resume_text = result.get(
                        "extracted_text",
                        "",
                    )
                    st.session_state.resume_skills = result.get(
                        "detected_skills",
                        [],
                    )

                    # Clear results from any previous resume.
                    st.session_state.ranked_jobs = []
                    st.session_state.skill_gap_results = {}
                    st.session_state.ranking_completed = False

                    st.success("Resume analyzed successfully!")

    if st.session_state.resume_text:
        st.divider()

        metric_col1, metric_col2 = st.columns(2)

        with metric_col1:
            st.metric(
                "Technical Skills Detected",
                len(st.session_state.resume_skills),
            )

        with metric_col2:
            st.metric(
                "Resume Word Count",
                len(st.session_state.resume_text.split()),
            )

        st.subheader("Detected Technical Skills")

        display_skill_tags(
            st.session_state.resume_skills,
        )

        with st.expander("View Extracted Resume Text"):
            st.text_area(
                "Resume Text",
                st.session_state.resume_text,
                height=280,
                disabled=True,
            )


# ----------------------------------
# Job Explorer
# ----------------------------------

with jobs_tab:
    st.header("Explore Job Opportunities")

    st.caption(
        "Search the job postings currently saved "
        "in your application's database."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        keyword = st.text_input(
            "Job Title or Keyword",
            placeholder="Python, Machine Learning, AI...",
        )

    with col2:
        location = st.text_input(
            "Location",
            placeholder="Remote, San Francisco...",
        )

    with col3:
        remote_option = st.selectbox(
            "Work Preference",
            [
                "All Jobs",
                "Remote Only",
                "On-Site Only",
            ],
        )

    if st.button(
        "Search Available Jobs",
        type="primary",
    ):
        params = {}

        if keyword.strip():
            params["keyword"] = keyword.strip()

        if location.strip():
            params["location"] = location.strip()

        if remote_option == "Remote Only":
            params["remote"] = True
        elif remote_option == "On-Site Only":
            params["remote"] = False

        with st.spinner("Searching saved job postings..."):
            jobs = api_request(
                "GET",
                "/jobs",
                params=params,
            )

        st.session_state.search_results = jobs

    if st.session_state.search_results is not None:
        jobs = st.session_state.search_results

        st.divider()

        st.metric("Jobs Found", len(jobs))

        if not jobs:
            st.info("No matching job postings found.")

        for job in jobs:
            with st.container(border=True):
                st.subheader(job.get("title", "Untitled Job"))

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.caption("COMPANY")
                    st.write(job.get("company", "Not specified"))

                with col_b:
                    st.caption("LOCATION")
                    st.write(job.get("location", "Not specified"))

                with col_c:
                    st.caption("WORK ARRANGEMENT")
                    st.write(
                        "Remote"
                        if job.get("remote")
                        else "On-site"
                    )

                with st.expander("View Job Description"):
                    st.write(
                        job.get(
                            "description",
                            "No description available.",
                        )
                    )


# ----------------------------------
# AI Job Recommendations
# ----------------------------------

with matches_tab:
    st.header("Your AI Job Recommendations")

    st.caption(
        "Rank saved job descriptions against your "
        "resume using semantic embeddings."
    )

    if not st.session_state.resume_text:
        st.warning(
            "Upload and analyze your resume "
            "before requesting recommendations."
        )

    else:
        st.success("Your resume is ready for matching.")

        if st.button(
            "Find My Best Matches",
            type="primary",
        ):
            with st.spinner("Ranking your job matches..."):
                result = api_request(
                    "POST",
                    "/rank-saved-jobs",
                    json={
                        "resume_text": (
                            st.session_state.resume_text
                        )
                    },
                )

            if result is not None:
                st.session_state.ranked_jobs = result.get(
                    "ranked_jobs",
                    [],
                )
                st.session_state.skill_gap_results = {}
                st.session_state.ranking_completed = True

        if st.session_state.ranking_completed:
            ranked_jobs = st.session_state.ranked_jobs

            if not ranked_jobs:
                st.info("No saved job postings were found.")

            else:
                ranked_jobs = sorted(
                    ranked_jobs,
                    key=lambda job: float(
                        job.get("match_score", 0)
                    ),
                    reverse=True,
                )

                scores = [
                    normalize_score(
                        job.get("match_score", 0)
                    )
                    for job in ranked_jobs
                ]

                best_job = ranked_jobs[0]
                best_score = scores[0]

                st.divider()
                st.subheader("Matching Overview")

                metric1, metric2, metric3, metric4 = st.columns(4)

                with metric1:
                    st.metric(
                        "Jobs Analyzed",
                        len(ranked_jobs),
                    )

                with metric2:
                    st.metric(
                        "Highest Similarity",
                        f"{best_score:.2f}%",
                    )

                with metric3:
                    st.metric(
                        "Average Similarity",
                        f"{sum(scores) / len(scores):.2f}%",
                    )

                with metric4:
                    st.metric(
                        "Skills on Resume",
                        len(st.session_state.resume_skills),
                    )

                st.info(
                    "Top semantic match: "
                    f"{best_job.get('title', 'Unknown')}. "
                    "Similarity scores describe text alignment, "
                    "not hiring probabilities."
                )

                st.subheader("Job Similarity Comparison")

                chart_data = pd.DataFrame(
                    {
                        "Job": [
                            (
                                f"{job.get('title', 'Untitled')} "
                                f"(ID {job.get('id', '?')})"
                            )
                            for job in ranked_jobs
                        ],
                        "Similarity (%)": scores,
                    }
                )

                st.bar_chart(
                    chart_data.set_index("Job"),
                    horizontal=True,
                    color="#3B82F6",
                )

                st.divider()
                st.subheader("Ranked Job Opportunities")

                for index, job in enumerate(
                    ranked_jobs,
                    start=1,
                ):
                    job_id = job.get("id", index)
                    score = normalize_score(
                        job.get("match_score", 0)
                    )

                    with st.container(border=True):
                        st.markdown(
                            f'<div class="rank-label">'
                            f'RANK #{index}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        st.subheader(
                            job.get("title", "Untitled Job")
                        )

                        st.markdown(
                            f'<div class="job-company">'
                            f'Company: '
                            f'{__import__("html").escape(str(job.get("company", "Unknown")))}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        left, right = st.columns([2, 1])

                        with left:
                            st.write(
                                f"**{similarity_label(score)}**"
                            )
                            st.progress(
                                score / 100,
                                text=f"Semantic Similarity: {score:.2f}%",
                            )

                        with right:
                            st.metric(
                                "Match Score",
                                f"{score:.2f}%",
                            )

                        with st.expander("View Job Description"):
                            st.write(
                                job.get(
                                    "description",
                                    "No description available.",
                                )
                            )

                        if st.button(
                            "Analyze Skill Gap",
                            key=f"skills_{job_id}",
                        ):
                            with st.spinner(
                                "Analyzing technical skills..."
                            ):
                                result = api_request(
                                    "POST",
                                    "/match",
                                    json={
                                        "resume_text": (
                                            st.session_state.resume_text
                                        ),
                                        "job_description": (
                                            job.get("description", "")
                                        ),
                                    },
                                )

                            if result is not None:
                                st.session_state.skill_gap_results[
                                    job_id
                                ] = result

                        if job_id in st.session_state.skill_gap_results:
                            gap = st.session_state.skill_gap_results[
                                job_id
                            ]

                            st.divider()
                            st.markdown("**Skill Gap Analysis**")

                            matching_skills = gap.get(
                                "matching_skills",
                                [],
                            )
                            missing_skills = gap.get(
                                "missing_skills",
                                [],
                            )

                            st.caption("MATCHING SKILLS")
                            display_skill_tags(matching_skills)

                            st.caption("MISSING SKILLS")
                            display_skill_tags(
                                missing_skills,
                                missing=True,
                            )

                            coverage = normalize_score(
                                gap.get("skill_coverage", 0)
                            )

                            st.progress(
                                coverage / 100,
                                text=(
                                    f"Technical Skill Coverage: "
                                    f"{coverage:.2f}%"
                                ),
                            )


st.divider()

st.caption(
    "Portfolio project built with Python, FastAPI, "
    "PostgreSQL, Streamlit, and sentence-transformer "
    "embeddings. Results are based on saved demo job "
    "postings and should not be interpreted as "
    "real-world hiring probabilities."
)
