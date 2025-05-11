from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# Get Hugging Face API token from environment
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

def generate_quiz(topic, difficulty, num_questions):
    # Example: Replace this with your real Hugging Face/OpenRouter API call
    # For now, returns dummy questions
    questions = []
    for i in range(1, int(num_questions) + 1):
        questions.append({
            "question": f"Sample Question {i} on {topic} ({difficulty.title()})",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "answer": "A",
            "explanation": f"This is a placeholder explanation for question {i}."
        })
    return questions

@app.route("/")
def index():
    # You will create templates/index.html later
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def quiz_api():
    data = request.json
    topic = data.get("topic", "General Knowledge")
    difficulty = data.get("difficulty", "medium")
    num_questions = data.get("num_questions", 5)
    quiz = generate_quiz(topic, difficulty, num_questions)
    return jsonify({"quiz": quiz})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
