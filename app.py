from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# --- Dummy quiz generation logic (replace with real API call later) ---
def generate_quiz(topic, difficulty, num_questions):
    questions = []
    for i in range(1, int(num_questions) + 1):
        questions.append({
            "question": f"Sample Question {i} on {topic} ({difficulty.title()})",
            "options": [
                "A. Option 1",
                "B. Option 2",
                "C. Option 3",
                "D. Option 4"
            ],
            "answer": "A",
            "explanation": f"This is a placeholder explanation for question {i}."
        })
    return questions

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def quiz_api():
    data = request.json
    topic = data.get("topic", "General Knowledge")
    difficulty = data.get("difficulty", "medium")
    num_questions = data.get("num_questions", 5)
    quiz = generate_quiz(topic, difficulty, num_questions)
    return jsonify({"quiz": quiz})

# --- For Railway/Render/Cloud deployment ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
