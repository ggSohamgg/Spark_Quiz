import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

# Set page config FIRST
st.set_page_config(
    page_title="SparkQuiz: AI-Powered Learning",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Custom CSS for a unique, modern interface
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

/* Global styles */
body, .main .block-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
    max-width: 1200px;
    margin: auto;
    padding: 20px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #1e293b;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    width: 300px;
}

/* Sidebar inputs */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background: #2d3748 !important;
    color: #e2e8f0 !important;
    border: 1px solid #4b5563 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    transition: all 0.3s ease;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] select:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 8px rgba(99, 102, 241, 0.3) !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
    color: #ffffff;
    font-weight: 600;
    border-radius: 10px;
    padding: 12px 24px;
    border: none;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.6);
}

/* Headings */
h1 {
    color: #a855f7;
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 10px;
}
h2, h3 {
    color: #e2e8f0;
    font-weight: 600;
}

/* Quiz card */
.quiz-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    transition: transform 0.3s ease;
    color: #e2e8f0;
    line-height: 1.6;
}
.quiz-card:hover {
    transform: translateY(-5px);
}

/* Info banner */
.info-banner {
    background: linear-gradient(90deg, #4b5563 0%, #6b7280 100%);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    color: #e2e8f0;
    text-align: center;
    font-size: 1rem;
}

/* Progress bar */
.progress-bar {
    background: #2d3748;
    border-radius: 10px;
    height: 8px;
    overflow: hidden;
    margin-top: 10px;
}
.progress-bar div {
    background: #6366f1;
    height: 100%;
    transition: width 0.5s ease;
}

/* Theme toggle */
.theme-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    cursor: pointer;
    font-size: 1.5rem;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.stMarkdown, .quiz-card {
    animation: fadeIn 0.5s ease-in;
}

/* Responsive design */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        width: 100%;
        border-radius: 0;
    }
    .main .block-container {
        padding: 10px;
    }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Hugging Face API configuration
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

def query_model(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 429:
            st.warning("Rate limit reached. Waiting before retrying...")
            time.sleep(5)
            return query_model(payload)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
        return response.json()
    except Exception as e:
        st.error(f"Error querying model: {str(e)}")
        return None

def generate_quiz(parameters):
    system_prompt = "You are a helpful quiz generator assistant. Create high-quality educational quizzes that are factually accurate."
    user_prompt = f"""
Generate a quiz with the following parameters:
- Topic: {parameters['topic']}
- Difficulty: {parameters['difficulty']}
- Number of questions: {parameters['num_questions']}
- Question types: {', '.join(parameters['question_types'])}
"""
    if parameters.get("subtopics"):
        user_prompt += f"- Sub-topics: {', '.join(parameters['subtopics'])}\n"
    if parameters.get("keywords"):
        user_prompt += f"- Context keywords: {', '.join(parameters['keywords'])}\n"
    if parameters.get("audience"):
        user_prompt += f"- Target audience: {parameters['audience']}\n"
    if parameters.get("language", "en") != "en":
        user_prompt += f"- Language: {parameters['language']}\n"
    user_prompt += f"- Include explanations: {'Yes' if parameters.get('include_explanations', False) else 'No'}\n"
    if parameters.get("max_length"):
        user_prompt += f"- Maximum length per question: {parameters['max_length']} words\n"
    user_prompt += """
Please format the quiz as follows:
1. Number each question
2. For multiple choice questions, label options as A, B, C, D
3. If explanations are requested, include them after each question
4. Make sure all information is factually correct
"""

    prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": min(1000, 150 * parameters['num_questions']),
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False
        }
    }

    # Simulate progress for better UX
    progress_bar = st.progress(0)
    with st.spinner("Crafting your quiz..."):
        start_time = time.time()
        for i in range(10):
            time.sleep(0.2)
            progress_bar.progress((i + 1) / 10)
        response = query_model(payload)
        generation_time = time.time() - start_time
        progress_bar.progress(1.0)

    if not response:
        return None, 0

    try:
        quiz_text = response[0]["generated_text"]
        return quiz_text, generation_time
    except (KeyError, IndexError, TypeError) as e:
        st.error(f"Unexpected API response format: {str(e)}")
        st.json(response)
        return None, 0

# App UI
st.title("✨ SparkQuiz: AI-Powered Learning")
st.markdown("""
<div class='info-banner'>
Create engaging, tailored quizzes on any topic with cutting-edge AI. Perfect for educators, students, and curious minds.
</div>
""", unsafe_allow_html=True)

# Theme toggle (placeholder for light/dark mode)
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
st.markdown(f"<div class='theme-toggle'>{'🌙' if st.session_state.theme == 'dark' else '☀️'}</div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("🎨 Quiz Builder")
topic = st.sidebar.text_input("Topic", placeholder="e.g., Quantum Physics, World History", help="Enter the main subject of your quiz")
difficulty = st.sidebar.selectbox("Difficulty", options=["Easy", "Medium", "Hard"], index=1, help="Choose the challenge level")
num_questions = st.sidebar.slider("Number of Questions", min_value=1, max_value=10, value=3, help="Select how many questions to generate")
question_types = st.sidebar.multiselect(
    "Question Types",
    options=["Multiple Choice", "True/False", "Short Answer"],
    default=["Multiple Choice"],
    help="Pick one or more question formats"
)

with st.sidebar.expander("🔧 Advanced Settings"):
    subtopics = st.text_input("Sub-topics (comma-separated)", placeholder="e.g., Wave-particle duality, Quantum entanglement")
    keywords = st.text_input("Keywords (comma-separated)", placeholder="e.g., experiment, theory, equation")
    audience = st.text_input("Target Audience", placeholder="e.g., High School Students")
    language = st.selectbox("Language", options=["English", "Spanish", "French", "German", "Chinese", "Japanese"], index=0)
    include_explanations = st.checkbox("Include Explanations", value=True, help="Add detailed answers for each question")
    max_length = st.number_input("Max Words per Question", min_value=0, value=0, help="Set a word limit (0 for no limit)")

# Generate button
if st.sidebar.button("🚀 Generate Quiz"):
    if not topic or not question_types:
        st.error("Please enter a topic and select at least one question type.")
    else:
        parameters = {
            "topic": topic,
            "difficulty": difficulty.lower(),
            "num_questions": int(num_questions),
            "question_types": [qt.lower() for qt in question_types],
            "include_explanations": include_explanations,
            "language": language[:2].lower() if language != "English" else "en"
        }
        if subtopics:
            parameters["subtopics"] = [s.strip() for s in subtopics.split(",")]
        if keywords:
            parameters["keywords"] = [k.strip() for s in keywords.split(",")]
        if audience:
            parameters["audience"] = audience
        if max_length > 0:
            parameters["max_length"] = max_length

        quiz_text, generation_time = generate_quiz(parameters)

        if quiz_text:
            st.markdown(f"<div class='quiz-card'>", unsafe_allow_html=True)
            st.markdown(f"## {topic} Quiz ({difficulty})")
            st.markdown(quiz_text)
            st.markdown("</div>", unsafe_allow_html=True)
            st.success(f"Quiz generated in {generation_time:.2f} seconds")
            quiz_download = f"# {topic} Quiz ({difficulty})\n\n{quiz_text}"
            st.download_button(
                label="📥 Download Quiz",
                data=quiz_download,
                file_name=f"{topic.replace(' ', '_').lower()}_quiz.md",
                mime="text/markdown"
            )
else:
    st.markdown("""
    <div class='quiz-card' style='text-align: center;'>
        <h3>Ready to Learn?</h3>
        <p>Configure your quiz in the sidebar and hit "Generate Quiz" to get started!</p>
    </div>
    """, unsafe_allow_html=True)

# About section
with st.expander("ℹ️ About SparkQuiz"):
    st.markdown("""
    SparkQuiz leverages **Qwen2.5-72B-Instruct**, a state-of-the-art model by Alibaba Cloud, hosted on Hugging Face's Inference API. 
    Create custom quizzes effortlessly for any subject, audience, or language.

    ### Why SparkQuiz?
    - **Flexible**: Tailor quizzes with specific topics, difficulties, and formats.
    - **Educational**: Explanations enhance learning and retention.
    - **Accessible**: No local GPU needed, powered by Hugging Face.
    - **Multilingual**: Generate quizzes in English, Spanish, French, and more.

    ### Usage Tips
    1. Choose a clear topic and question types.
    2. Use advanced settings for precise control.
    3. Download your quiz for offline use.
    4. Note: Free-tier API has a 300 requests/day limit.

    For feedback or issues, check the model card: [Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct).
    """)