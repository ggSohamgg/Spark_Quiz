from flask import Flask, render_template, request, jsonify
import os
import requests
import re

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

def generate_quiz(parameters):
    # Build prompt from parameters
    prompt = f"Generate a quiz with the following parameters:\n"
    prompt += f"- Topic: {parameters['topic']}\n"
    prompt += f"- Difficulty: {parameters['difficulty']}\n"
    prompt += f"- Number of questions: {parameters['num_questions']}\n"
    prompt += f"- Question types: {', '.join(parameters['question_types'])}\n"
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
    prompt += (
        "Please format the quiz as follows:\n"
        "1. Number each question\n"
        "2. For multiple choice questions, label options as A, B, C, D\n"
        "3. If explanations are requested, include them after each question\n"
        "4. Make sure all information is factually correct\n"
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
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
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
        if response.status_code == 200:
            data = response.json().get("data", {})
            used = data.get("usage", 0)
            limit = data.get("limit")
            rate_limit = data.get("rate_limit", {})
            per_min = rate_limit.get("requests")
            interval = rate_limit.get("interval")
            if limit is not None:
                remaining = limit - used
            else:
                remaining = None
            return {
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "is_free_tier": data.get("is_free_tier", True),
                "per_min": per_min,
                "interval": interval
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
    parameters = request.json
    quiz = generate_quiz(parameters)
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
