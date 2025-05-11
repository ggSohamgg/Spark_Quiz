from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"

def generate_quiz(topic, difficulty, num_questions):
    prompt = (
        f"Generate a {num_questions}-question {difficulty} quiz on the topic '{topic}'. "
        "For each question, provide 4 options labeled A-D, the correct answer, and a brief explanation."
    )
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": min(1000, 150 * int(num_questions)),
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False
        }
    }
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        # The API returns a list of dicts; get the generated text
        quiz_text = data[0]["generated_text"]
        # Parse the text into structured questions for the frontend
        questions = parse_quiz_text(quiz_text)
        return questions
    except Exception as e:
        print(f"Error from Hugging Face API: {e}")
        # Fallback: return a single error question
        return [{
            "question": "Sorry, the quiz could not be generated at this time.",
            "options": [],
            "answer": "",
            "explanation": str(e)
        }]

def parse_quiz_text(quiz_text):
    """
    Parses the quiz text from the model into a list of question dicts.
    This is a simple parser; you may want to improve it for more robust formatting.
    """
    questions = []
    # Split by question number (e.g., "1.", "2.", etc.)
    import re
    q_blocks = re.split(r"\n?\s*\d+\.\s*", quiz_text)
    for block in q_blocks:
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        q = {"question": "", "options": [], "answer": "", "explanation": ""}
        # Find options (A., B., etc.)
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
                # Append to explanation if not already set as question/options/answer
                if q["explanation"]:
                    q["explanation"] += " " + line.strip()
        questions.append(q)
    return questions

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
