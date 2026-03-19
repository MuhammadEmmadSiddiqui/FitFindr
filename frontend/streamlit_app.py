"""FitFindr Streamlit frontend — communicates with the FastAPI backend over HTTP."""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import httpx

# ─── Backend base URL ─────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FitFindr - AI Resume Screening",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header { font-size:2.5rem; font-weight:bold; color:#1f77b4;
               text-align:center; margin-bottom:2rem; }
.metric-card { background:#f0f2f6; padding:1.5rem;
               border-radius:0.5rem; margin:0.5rem 0; }
.candidate-card { border:1px solid #ddd; border-radius:8px;
                  padding:1rem; margin:0.5rem 0; background:#fff; }
div[data-testid="stMetricValue"] { font-size:2rem; }
</style>
""", unsafe_allow_html=True)


# ─── Session-state defaults ────────────────────────────────────────────────────
def _init_session():
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("auth_page", "login")   # "login" | "register"

_init_session()


# ─── HTTP helpers ──────────────────────────────────────────────────────────────
def _auth_header() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def _post(path: str, **kwargs) -> httpx.Response:
    return httpx.post(f"{API_BASE}{path}", timeout=120, **kwargs)


def _get(path: str, **kwargs) -> httpx.Response:
    return httpx.get(f"{API_BASE}{path}", timeout=30,
                     headers=_auth_header(), **kwargs)


# ─── Auth pages ───────────────────────────────────────────────────────────────
def _page_login():
    st.markdown('<div class="main-header">🎯 FitFindr</div>', unsafe_allow_html=True)
    col, _ = st.columns([1, 1])
    with col:
        st.subheader("Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Sign In", use_container_width=True):
            if not username or not password:
                st.warning("Please enter username and password.")
            else:
                resp = _post(
                    "/auth/login",
                    data={"username": username, "password": password},
                )
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    detail = resp.json().get("detail", "Login failed")
                    st.error(f"❌ {detail}")

        st.markdown("---")
        st.caption("Don't have an account?")
        if st.button("Create Account", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()


def _page_register():
    st.markdown('<div class="main-header">🎯 FitFindr</div>', unsafe_allow_html=True)
    col, _ = st.columns([1, 1])
    with col:
        st.subheader("Create Account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Register", use_container_width=True):
            if not all([username, email, password, confirm]):
                st.warning("All fields are required.")
            elif password != confirm:
                st.warning("Passwords do not match.")
            else:
                resp = _post(
                    "/auth/register",
                    json={"username": username, "email": email, "password": password},
                )
                if resp.status_code == 201:
                    st.success("✅ Account created — please sign in.")
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    detail = resp.json().get("detail", "Registration failed")
                    st.error(f"❌ {detail}")

        st.markdown("---")
        st.caption("Already have an account?")
        if st.button("Sign In", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ─── Main app (authenticated) ─────────────────────────────────────────────────
def _page_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.username}**")
        if st.button("Sign Out"):
            st.session_state.token = None
            st.session_state.username = None
            st.rerun()

        st.header("📤 Upload Files")
        st.markdown("---")

        st.subheader("⚙️ Settings")
        show_advanced = st.checkbox("Show advanced analytics", value=True)
        st.markdown("---")

        jd_file = st.file_uploader(
            "Upload Job Description", type=["txt", "pdf"],
            help="Upload the job description in TXT or PDF format",
        )
        resume_files = st.file_uploader(
            "Upload Resumes", type=["txt", "pdf"],
            accept_multiple_files=True,
            help="Upload one or multiple resumes in TXT or PDF format",
        )
        st.markdown("---")

        st.subheader("ℹ️ About")
        st.info("""
**FitFindr v1.0**

- AI-powered resume matching
- BERT semantic similarity
- Structured data extraction
- Advanced analytics
        """)

    st.markdown('<div class="main-header">🎯 FitFindr — AI-Powered Resume Screening</div>',
                unsafe_allow_html=True)

    # ── Screening ────────────────────────────────────────────────────────────
    if jd_file and resume_files:
        with st.spinner("🔍 Processing resumes… this may take a moment."):
            try:
                files = [("job_description", (jd_file.name, jd_file.getvalue(), jd_file.type))]
                for rf in resume_files:
                    files.append(("resumes", (rf.name, rf.getvalue(), rf.type)))

                resp = httpx.post(
                    f"{API_BASE}/api/screen",
                    files=files,
                    headers=_auth_header(),
                    timeout=300,
                )
                if resp.status_code == 401:
                    st.error("Session expired — please sign in again.")
                    st.session_state.token = None
                    st.rerun()
                if resp.status_code != 200:
                    st.error(f"❌ Backend error {resp.status_code}: {resp.json().get('detail')}")
                    return

                data = resp.json()
                results = data["results"]

                if not results:
                    st.warning("⚠️ No results returned — the files may be unreadable or the LLM service is unavailable.")
                    return

                results_df = pd.DataFrame(results)

            except httpx.ConnectError:
                st.error("❌ Cannot reach the backend. Is the FastAPI server running on port 8000?")
                return
            except Exception as exc:
                st.error(f"❌ Unexpected error: {exc}")
                return

        # Metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Resumes", len(results))
        with col2:
            st.metric("📈 Avg. Match Score",
                      f"{results_df['similarity_score'].mean():.2%}")
        with col3:
            st.metric("⭐ Top Match",
                      f"{results_df['similarity_score'].max():.2%}")
        with col4:
            qualified = len(results_df[results_df["similarity_score"] > 0.7])
            st.metric("✅ High Match (>70%)", qualified)

        st.markdown("---")

        # Top candidates
        st.subheader("🏆 Top Candidates")
        for idx, r in enumerate(results[:5], 1):
            with st.expander(
                f"#{idx} — {r['full_name']} | Match: {r['similarity_score']:.1%}",
                expanded=(idx == 1),
            ):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**📄 Resume:** {r['resume_filename']}")
                    st.markdown(f"**🎓 University:** {r['university_name']}")
                    st.markdown(f"**📧 Email:** {r['email_id']}")
                    st.markdown(f"**🔗 GitHub:** {r['github_link']}")
                    st.markdown(f"**📍 Location:** {r['location']}")
                with col2:
                    st.markdown(f"**💼 Experience:** {r['total_experience']}")
                    st.markdown("**🏢 Companies:**")
                    for company in r.get("company_names", [])[:3]:
                        st.markdown(f"- {company}")
                if r.get("technical_skills"):
                    st.markdown("**🛠️ Technical Skills:**")
                    st.markdown(", ".join(r["technical_skills"][:10]))
                if r.get("soft_skills"):
                    st.markdown("**💡 Soft Skills:**")
                    st.markdown(", ".join(r["soft_skills"][:8]))

        # All candidates table
        st.markdown("---")
        st.subheader("📋 All Candidates")
        display_df = results_df[[
            "resume_filename", "similarity_score", "full_name",
            "university_name", "email_id", "total_experience", "location",
        ]].copy()
        display_df["similarity_score"] = display_df["similarity_score"].apply(
            lambda x: f"{x:.2%}"
        )
        display_df.columns = ["Resume", "Match %", "Name", "University",
                              "Email", "Experience", "Location"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button(
            "📥 Download Full Results (CSV)",
            data=results_df.to_csv(index=False),
            file_name="screening_results.csv",
            mime="text/csv",
        )

        # Advanced analytics
        if show_advanced:
            st.markdown("---")
            st.subheader("📊 Advanced Analytics")
            tab1, tab2, tab3 = st.tabs(
                ["📈 Score Distribution", "🎓 University Analysis", "🛠️ Skills Cloud"]
            )

            with tab1:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
                ax1.hist(results_df["similarity_score"], bins=20,
                         color="skyblue", edgecolor="black")
                ax1.set(xlabel="Similarity Score", ylabel="Frequency",
                        title="Score Distribution")
                ax1.grid(alpha=0.3)
                ax2.boxplot(results_df["similarity_score"])
                ax2.set(ylabel="Similarity Score", title="Score Statistics")
                ax2.grid(alpha=0.3)
                st.pyplot(fig)
                plt.close()

            with tab2:
                uni_counts = results_df["university_name"].value_counts().head(10)
                if len(uni_counts) > 0:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.barplot(x=uni_counts.values, y=uni_counts.index,
                                palette="viridis", ax=ax)
                    ax.set(xlabel="Number of Candidates", ylabel="University",
                           title="Top 10 Universities")
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("Not enough data for university analysis")

            with tab3:
                all_skills = [
                    skill
                    for row in results_df["technical_skills"]
                    if isinstance(row, list)
                    for skill in row
                ]
                if all_skills:
                    wc = WordCloud(width=1200, height=600, background_color="white",
                                   colormap="viridis").generate(" ".join(all_skills))
                    fig, ax = plt.subplots(figsize=(14, 7))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    ax.set_title("Technical Skills Word Cloud", fontsize=16, pad=20)
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("No technical skills data available")

            # Interactive filters
            st.markdown("---")
            st.subheader("🔍 Filter Candidates")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                min_score = st.slider("Minimum Match Score", 0.0, 1.0, 0.5)
            with fc2:
                selected_unis = st.multiselect(
                    "Universities", options=results_df["university_name"].unique().tolist()
                )
            with fc3:
                all_tech = sorted({
                    s for row in results_df["technical_skills"]
                    if isinstance(row, list) for s in row
                })
                selected_skills = st.multiselect("Required Skills", options=all_tech)

            filtered = results_df[results_df["similarity_score"] >= min_score]
            if selected_unis:
                filtered = filtered[filtered["university_name"].isin(selected_unis)]
            if selected_skills:
                filtered = filtered[filtered["technical_skills"].apply(
                    lambda x: any(s in x for s in selected_skills) if isinstance(x, list) else False
                )]

            st.markdown(f"**Showing {len(filtered)} of {len(results_df)} candidates**")
            if len(filtered):
                st.dataframe(
                    filtered[["resume_filename", "similarity_score", "full_name",
                               "university_name", "total_experience"]],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.warning("No candidates match the selected filters")

    else:
        # Welcome / recent results
        st.info("""
👋 **Welcome to FitFindr!**

Get started by uploading:
1. 📄 **Job Description** — the role you're hiring for
2. 📚 **Resumes** — candidate resumes to screen

The AI will analyse and rank candidates based on their fit for the role.
        """)

        with st.expander("📖 How it works"):
            st.markdown("""
**FitFindr uses advanced AI to streamline your hiring:**

1. **Upload Documents** — Add job description and candidate resumes
2. **AI Analysis** — BERT embeddings calculate semantic similarity
3. **Data Extraction** — LLM extracts structured information from resumes
4. **Smart Ranking** — Candidates are ranked by relevance
5. **Deep Insights** — Analytics on skills, experience, and more

**Technologies:** BERT · Llama 3 · Docling · instructor · FastAPI · SQLite
            """)

        with st.expander("📜 View Recent Screenings"):
            try:
                resp = _get("/api/results", params={"limit": 20})
                if resp.status_code == 200:
                    recent = resp.json()
                    if recent:
                        recent_df = pd.DataFrame([{
                            "Date": r["screening_date"],
                            "Resume": r["resume_filename"],
                            "Name": r["full_name"],
                            "Score": f"{r['similarity_score']:.2%}",
                            "University": r["university_name"],
                        } for r in recent])
                        st.dataframe(recent_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No recent screenings found")
                elif resp.status_code == 401:
                    st.warning("Session expired — please sign in again.")
                    st.session_state.token = None
                    st.rerun()
            except httpx.ConnectError:
                st.warning("Backend unavailable — cannot load recent screenings.")


# ─── Router ───────────────────────────────────────────────────────────────────
if not st.session_state.token:
    if st.session_state.auth_page == "register":
        _page_register()
    else:
        _page_login()
else:
    _page_app()

