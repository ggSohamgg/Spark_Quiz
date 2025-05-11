from flask import Flask, render_template, request, jsonify
import os
import requests
import re

# Initialize Flask app
app = Flask(__name__)

# Load OpenRouter API key from environment variable
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# OpenRouter API endpoint and model name
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

def generate_quiz(parameters):
    """
    Build a prompt from user parameters, send it to the OpenRouter API,
    and parse the response into a list of questions.
    """
    # Start building the prompt for the LLM
    prompt = f"Generate a quiz with the following parameters:\n"
    prompt += f"- Topic: {parameters['topic']}\n"
    prompt += f"- Difficulty: {parameters['difficulty']}\n"
    # Add each question type and its requested count
    type_lines = []
    for t in parameters['question_types']:
        count = parameters['type_counts'].get(t, 1)
        type_lines.append(f"{t} ({count})")
    prompt += f"- Question types: {', '.join(type_lines)}\n"
    # Optional fields
    if parameters.get("subtopics"):
        prompt += f"- Sub-topics: {', '.join(parameters['subtopics'])}\n"
    if parameters.get("keywords"):
        prompt += f"- Context keywords: {', '.join(parameters['keywords'])}\n"
    if parameters.get("audience"):
        prompt += f"- Target audience: {parameters['audience']}\n"
    if parameters.get("language", "en") != "en":
        prompt += f"- Language: {parameters['language']}\n"
    prompt += f"- Include explanations: {'Yes' if parameters.get('include_explanations', False) else 'No'}\n"
    if parameters.get("max_length"):
        prompt += f"- Maximum length per question: {parameters['max_length']} words\n"
    # Add instructions for output format
    prompt += (
        "Please format the quiz as follows:\n"
        "1. Number each question\n"
        "2. For multiple choice questions, label options as A, B, C, D\n"
        "3. If explanations are requested, include them after each question\n"
        "4. Make sure all information is factually correct\n"
    )

    # Prepare headers and payload for the OpenRouter API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        # Send the prompt to OpenRouter and get the response
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        # Extract the quiz text from the API response
        quiz_text = data["choices"][0]["message"]["content"]
        # Parse the quiz text into structured questions
        questions = parse_quiz_text(quiz_text)
        return questions
    except Exception as e:
        # If an error occurs, return a single error question
        print(f"Error from OpenRouter API: {e}")
        return [{
            "question": "Sorry, the quiz could not be generated at this time.",
            "options": [],
            "answer": "",
            "explanation": str(e)
        }]

def parse_quiz_text(quiz_text):
    """
    Parse the quiz text returned by the LLM into a list of question dictionaries.
    Each question may have options, an answer, and an explanation.
    """
    questions = []
    # Split the text into question blocks using regex for numbered questions
    q_blocks = re.split(r"\n?\s*\d+\.\s*", quiz_text)
    for block in q_blocks:
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        q = {"question": "", "options": [], "answer": "", "explanation": ""}
        for line in lines:
            # Detect options (A., B., etc.)
            if re.match(r"^[A-D]\.", line.strip()):
                q["options"].append(line.strip())
            # Detect answer line
            elif line.lower().startswith("answer:"):
                q["answer"] = line.split(":", 1)[-1].strip()
            # Detect explanation line
            elif line.lower().startswith("explanation:"):
                q["explanation"] = line.split(":", 1)[-1].strip()
            # The first non-option, non-answer, non-explanation line is the question text
            elif not q["question"]:
                q["question"] = line.strip()
            # If there is extra explanation text, append it
            else:
                if q["explanation"]:
                    q["explanation"] += " " + line.strip()
        questions.append(q)
    return questions

@app.route("/")
def index():
    """
    Render the main SparkQuiz HTML page.
    """
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def quiz_api():
    """
    Receive quiz parameters from the frontend, generate the quiz, and return as JSON.
    """
    parameters = request.json
    quiz = generate_quiz(parameters)
    return jsonify({"quiz": quiz})

if __name__ == "__main__":
    # Run the Flask app (for development only; use a production WSGI server for deployment)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
