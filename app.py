from flask import Flask, render_template, request, jsonify
import os
import requests
import re

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

def generate_quiz(topic, difficulty, num_questions):
    prompt = (
        f"Generate a {num_questions}-question {difficulty} quiz on the topic '{topic}'. "
        "For each question, provide 4 options labeled A-D, the correct answer, and a brief explanation. "
        "Format:\n1. Question\nA. Option\nB. Option\nC. Option\nD. Option\nAnswer: ...\nExplanation: ..."
    )
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
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        quiz_text = data["choices"][0]["message"]["content"]
        questions = parse_quiz_text(quiz_text)
        return questions
    except Exception as e:
        print(f"Error from OpenRouter API: {e}")
        return [{
            "question": "Sorry, the quiz could not be generated at this time.",
            "options": [],
            "answer": "",
            "explanation": str(e)
        }]

def parse_quiz_text(quiz_text):
    questions = []
    q_blocks = re.split(r"\n?\s*\d+\.\s*", quiz_text)
    for block in q_blocks:
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        q = {"question": "", "options": [], "answer": "", "explanation": ""}
        for line in lines:
            if re.match(r"^[A-D]\.", line.strip()):
                q["options"].append(line.strip())
            elif line.lower().startswith("answer:"):
                q["answer"] = line.split(":", 1)[-1].strip()
            elif line.lower().startswith("explanation:"):
                q["explanation"] = line.split(":", 1)[-1].strip()
            elif not q["question"]:
                q["question"] = line.strip()
            else:
                if q["explanation"]:
                    q["explanation"] += " " + line.strip()
        questions.append(q)
    return questions

def get_openrouter_usage():
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print("USAGE DEBUG:", response.status_code, response.text)  # Debug info for logs
        if response.status_code == 200:
            data = response.json().get("data", {})
            used = data.get("usage", 0)
            limit = data.get("limit", 50)
            remaining = limit - used
            return {
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "is_free_tier": data.get("is_free_tier", True)
            }
        else:
            return None
    except Exception as e:
        print(f"Error checking usage: {e}")
        return None

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

@app.route("/usage")
def usage():
    usage_info = get_openrouter_usage()
    if usage_info:
        return jsonify(usage_info)
    else:
        return jsonify({"error": "Could not retrieve usage info"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
