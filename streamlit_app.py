"""Improved Streamlit UI for FitFindr"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.utils import setup_logging, get_logger
from src.services import ScreeningService
from src.database import init_db, get_db
from src.database.repository import ScreeningRepository

# Setup
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE, settings.LOGS_DIR)
logger = get_logger(__name__)
init_db()

# Page config
st.set_page_config(
    page_title="FitFindr - AI Resume Screening",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .candidate-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🎯 FitFindr - AI-Powered Resume Screening</div>', 
            unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📤 Upload Files")
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Settings")
    save_to_db = st.checkbox("Save results to database", value=True)
    show_advanced = st.checkbox("Show advanced analytics", value=True)
    
    st.markdown("---")
    
    # File uploads
    jd_file = st.file_uploader(
        "Upload Job Description",
        type=["txt", "pdf"],
        help="Upload the job description in TXT or PDF format"
    )
    
    resume_files = st.file_uploader(
        "Upload Resumes",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Upload one or multiple resumes in TXT or PDF format"
    )
    
    st.markdown("---")
    
    # App info
    st.subheader("ℹ️ About")
    st.info(f"""
    **Version:** {settings.APP_VERSION}
    
    **Features:**
    - AI-powered resume matching
    - BERT embeddings for similarity
    - Structured data extraction
    - Database persistence
    - Advanced analytics
    """)

# Main content
if jd_file and resume_files:
    with st.spinner("🔍 Processing resumes... This may take a moment."):
        try:
            # Initialize service
            screening_service = ScreeningService()
            
            # Prepare resume data
            resume_data = []
            for resume_file in resume_files:
                resume_data.append((
                    resume_file,
                    resume_file.name,
                    resume_file.type
                ))
            
            # Process screening
            results = screening_service.screen_multiple_resumes(
                resume_data,
                jd_file,
                jd_file.type
            )
            
            # Save to database if enabled
            if save_to_db:
                db = next(get_db())
                try:
                    jd_content = jd_file.getvalue().decode('utf-8', errors='ignore')
                    jd_db = ScreeningRepository.create_or_get_job_description(
                        db, jd_file.name, jd_content
                    )
                    
                    for result in results:
                        ScreeningRepository.save_screening_result(db, result, jd_db.id)
                    
                    st.success("✅ Results saved to database")
                except Exception as e:
                    logger.error(f"Database save error: {str(e)}")
                    st.warning("⚠️ Could not save to database")
                finally:
                    db.close()
            
            # Convert to DataFrame
            results_df = pd.DataFrame([r.dict() for r in results])
            
            # Display metrics
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Total Resumes", len(results))
            with col2:
                avg_score = results_df['similarity_score'].mean()
                st.metric("📈 Avg. Match Score", f"{avg_score:.2%}")
            with col3:
                top_score = results_df['similarity_score'].max()
                st.metric("⭐ Top Match", f"{top_score:.2%}")
            with col4:
                qualified = len(results_df[results_df['similarity_score'] > 0.7])
                st.metric("✅ High Match (>70%)", qualified)
            
            st.markdown("---")
            
            # Top Candidates Section
            st.subheader("🏆 Top Candidates")
            
            for idx, result in enumerate(results[:5], 1):
                with st.expander(
                    f"#{idx} - {result.full_name} | Match: {result.similarity_score:.1%}",
                    expanded=(idx == 1)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**📄 Resume:** {result.resume_filename}")
                        st.markdown(f"**🎓 University:** {result.university_name}")
                        st.markdown(f"**📧 Email:** {result.email_id}")
                        st.markdown(f"**🔗 GitHub:** {result.github_link}")
                        st.markdown(f"**📍 Location:** {result.location}")
                    
                    with col2:
                        st.markdown(f"**💼 Experience:** {result.total_experience}")
                        st.markdown(f"**🏢 Companies:**")
                        for company in result.company_names[:3]:
                            st.markdown(f"- {company}")
                    
                    # Skills
                    if result.technical_skills:
                        st.markdown("**🛠️ Technical Skills:**")
                        st.markdown(", ".join(result.technical_skills[:10]))
                    
                    if result.soft_skills:
                        st.markdown("**💡 Soft Skills:**")
                        st.markdown(", ".join(result.soft_skills[:8]))
            
            # Full Results Table
            st.markdown("---")
            st.subheader("📋 All Candidates")
            
            # Prepare display dataframe
            display_df = results_df[[
                'resume_filename', 'similarity_score', 'full_name',
                'university_name', 'email_id', 'total_experience', 'location'
            ]].copy()
            
            display_df['similarity_score'] = display_df['similarity_score'].apply(
                lambda x: f"{x:.2%}"
            )
            display_df.columns = [
                'Resume', 'Match %', 'Name', 'University',
                'Email', 'Experience', 'Location'
            ]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Results (CSV)",
                data=csv,
                file_name="screening_results.csv",
                mime="text/csv"
            )
            
            # Advanced Analytics
            if show_advanced:
                st.markdown("---")
                st.subheader("📊 Advanced Analytics")
                
                tab1, tab2, tab3 = st.tabs([
                    "📈 Score Distribution",
                    "🎓 University Analysis",
                    "🛠️ Skills Cloud"
                ])
                
                with tab1:
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
                    
                    # Histogram
                    ax1.hist(results_df['similarity_score'], bins=20, 
                            color='skyblue', edgecolor='black')
                    ax1.set_xlabel('Similarity Score')
                    ax1.set_ylabel('Frequency')
                    ax1.set_title('Score Distribution')
                    ax1.grid(alpha=0.3)
                    
                    # Box plot
                    ax2.boxplot(results_df['similarity_score'], vert=True)
                    ax2.set_ylabel('Similarity Score')
                    ax2.set_title('Score Statistics')
                    ax2.grid(alpha=0.3)
                    
                    st.pyplot(fig)
                    plt.close()
                
                with tab2:
                    uni_counts = results_df['university_name'].value_counts().head(10)
                    
                    if len(uni_counts) > 0:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        sns.barplot(x=uni_counts.values, y=uni_counts.index, 
                                  palette="viridis", ax=ax)
                        ax.set_xlabel('Number of Candidates')
                        ax.set_ylabel('University')
                        ax.set_title('Top 10 Universities')
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Not enough data for university analysis")
                
                with tab3:
                    all_skills = []
                    for skills_list in results_df['technical_skills']:
                        if isinstance(skills_list, list):
                            all_skills.extend(skills_list)
                    
                    if all_skills:
                        wordcloud = WordCloud(
                            width=1200,
                            height=600,
                            background_color='white',
                            colormap='viridis'
                        ).generate(' '.join(all_skills))
                        
                        fig, ax = plt.subplots(figsize=(14, 7))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        ax.set_title('Technical Skills Word Cloud', 
                                   fontsize=16, pad=20)
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("No technical skills data available")
            
            # Interactive Filters
            st.markdown("---")
            st.subheader("🔍 Filter Candidates")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_score = st.slider(
                    "Minimum Match Score",
                    0.0, 1.0, 0.5,
                    help="Filter candidates by minimum similarity score"
                )
            
            with col2:
                selected_unis = st.multiselect(
                    "Universities",
                    options=results_df['university_name'].unique().tolist(),
                    help="Filter by university"
                )
            
            with col3:
                all_tech_skills = set()
                for skills in results_df['technical_skills']:
                    if isinstance(skills, list):
                        all_tech_skills.update(skills)
                
                selected_skills = st.multiselect(
                    "Required Skills",
                    options=sorted(list(all_tech_skills)),
                    help="Filter by technical skills"
                )
            
            # Apply filters
            filtered_df = results_df[results_df['similarity_score'] >= min_score]
            
            if selected_unis:
                filtered_df = filtered_df[
                    filtered_df['university_name'].isin(selected_unis)
                ]
            
            if selected_skills:
                filtered_df = filtered_df[
                    filtered_df['technical_skills'].apply(
                        lambda x: any(skill in x for skill in selected_skills) 
                        if isinstance(x, list) else False
                    )
                ]
            
            st.markdown(f"**Showing {len(filtered_df)} of {len(results_df)} candidates**")
            
            if len(filtered_df) > 0:
                filtered_display = filtered_df[[
                    'resume_filename', 'similarity_score', 'full_name',
                    'university_name', 'total_experience'
                ]].copy()
                
                filtered_display['similarity_score'] = filtered_display['similarity_score'].apply(
                    lambda x: f"{x:.2%}"
                )
                
                st.dataframe(filtered_display, use_container_width=True, hide_index=True)
            else:
                st.warning("No candidates match the selected filters")
        
        except Exception as e:
            st.error(f"❌ Error processing resumes: {str(e)}")
            logger.error(f"Processing error: {str(e)}", exc_info=True)

else:
    # Welcome message
    st.info("""
    👋 **Welcome to FitFindr!**
    
    Get started by uploading:
    1. 📄 **Job Description** - The role you're hiring for
    2. 📚 **Resumes** - Candidate resumes to screen
    
    The AI will analyze and rank candidates based on their fit for the role.
    """)
    
    # Sample workflow
    with st.expander("📖 How it works"):
        st.markdown("""
        **FitFindr uses advanced AI to streamline your hiring:**
        
        1. **Upload Documents** - Add job description and candidate resumes
        2. **AI Analysis** - BERT embeddings calculate semantic similarity
        3. **Data Extraction** - LLM extracts structured information from resumes
        4. **Smart Ranking** - Candidates are ranked by relevance
        5. **Deep Insights** - View analytics on skills, experience, and more
        
        **Technologies:**
        - 🤖 BERT for semantic understanding
        - 🧠 Llama 3 for information extraction
        - 📊 Advanced analytics and visualizations
        - 💾 Database persistence for historical tracking
        """)
    
    # Recent results
    with st.expander("📜 View Recent Screenings"):
        try:
            db = next(get_db())
            recent_results = ScreeningRepository.get_recent_screenings(db, days=7, limit=20)
            
            if recent_results:
                recent_df = pd.DataFrame([{
                    'Date': r.screening_date.strftime('%Y-%m-%d %H:%M'),
                    'Resume': r.resume_filename,
                    'Name': r.full_name,
                    'Score': f"{r.similarity_score:.2%}",
                    'University': r.university_name
                } for r in recent_results])
                
                st.dataframe(recent_df, use_container_width=True, hide_index=True)
            else:
                st.info("No recent screenings found")
            
            db.close()
        except Exception as e:
            st.warning("Could not load recent screenings")
            logger.error(f"Error loading recent results: {str(e)}")
