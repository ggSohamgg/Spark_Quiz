from flask import Flask, render_template, request, jsonify
import os
import requests
import re

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

def generate_quiz(parameters):
    """
    Build the prompt from user parameters, send to OpenRouter API,
    and parse the response into a list of questions.
    """
    # Validate that at least one question is requested
    total_questions = sum(parameters['type_counts'].get(t, 0) for t in parameters['question_types'])
    if total_questions <= 0:
        return [{
            "question": "Error: Please request at least one question.",
            "options": [],
            "answer": "",
            "explanation": "No questions were requested. Please select at least one question type with a quantity greater than 0.",
            "type": ""
        }]

    # Check if API key is set
    if not OPENROUTER_API_KEY:
        return [{
            "question": "Error: API key not configured.",
            "options": [],
            "answer": "",
            "explanation": "The OPENROUTER_API_KEY environment variable is not set. Please configure it to use the OpenRouter API.",
            "type": ""
        }]

    prompt = f"Generate a quiz with the following parameters:\n"
    prompt += f"- Topic: {parameters['topic']}\n"
    prompt += f"- Difficulty: {parameters['difficulty']}\n"
    type_lines = []
    for t in parameters['question_types']:
        count = parameters['type_counts'].get(t, 1)
        type_lines.append(f"{t} ({count})")
    prompt += f"- Question types: {', '.join(type_lines)}\n"
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
        "1. Start with a heading like ### Topic Quiz\n"
        "2. For each question, use a subheading like #### Question X: Type (e.g., #### Question 1: Multiple Choice)\n"
        "3. For multiple choice questions, label options as A), B), C), D)\n"
        "4. If explanations are requested, include them after each question\n"
        "5. Make sure all information is factually correct\n"
        "6. Ensure each question's answer matches its explanation, and place the explanation after the answer.\n"
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
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        quiz_text = data["choices"][0]["message"]["content"]
        print(f"Raw API Response: {quiz_text}")  # Debug: Log the raw response
        questions = parse_quiz_text(quiz_text)
        if not questions:
            return [{
                "question": "Error: No questions generated.",
                "options": [],
                "answer": "",
                "explanation": "The API did not return any valid questions. This might be due to rate limits (10 requests/min, 50/day) or an unexpected response format.",
                "type": ""
            }]
        return questions
    except requests.exceptions.RequestException as e:
        print(f"Error from OpenRouter API: {e}")
        return [{
            "question": "Error: Failed to generate quiz.",
            "options": [],
            "answer": "",
            "explanation": f"API request failed: {str(e)}. This might be due to rate limits (10 requests/min, 50/day) or an invalid API key.",
            "type": ""
        }]

def parse_quiz_text(quiz_text):
    """
    Parse the quiz text returned by the LLM into a list of question dictionaries.
    Each question includes its type, options, answer, and explanation.
    """
    if not quiz_text or not quiz_text.strip():
        print("Debug: quiz_text is empty or None")
        return []  # Return empty list if quiz_text is empty

    questions = []
    # Split the text into sections based on #### headings, preserving the headings in the split
    # Use re.MULTILINE flag instead of embedding (?m) in the pattern
    sections = re.split(r"(?=^####\s.*$)", quiz_text, flags=re.MULTILINE)
    sections = [section.strip() for section in sections if section.strip()]
    print(f"Debug: Split sections: {sections}")

    # The first section might be the topic heading (### Topic Quiz), remove it if present
    if sections and sections[0].startswith("###"):
        sections.pop(0)

    # Process each section as a question block
    for section in sections:
        # Extract the question heading (#### Question X: Type)
        heading_match = re.match(r"####\s*Question\s*\d+:\s*(Multiple Choice|Short Answer|True/False)", section, re.IGNORECASE)
        if not heading_match:
            print(f"Debug: Skipping section, no valid heading found: {section[:100]}...")
            continue

        question_type = heading_match.group(1)
        # Remove the heading from the section content
        section_content = section[heading_match.end():].strip()
        print(f"Debug: Processing section for type {question_type}: {section_content[:100]}...")

        q = {"question": "", "options": [], "answer": "", "explanation": "", "type": question_type}
        lines = section_content.split("\n")
        in_options = False
        in_explanation = False

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Detect the question text (first non-empty line after the heading, or wrapped in **)
            if not q["question"]:
                if line.startswith("**") and line.endswith("**"):
                    q["question"] = line.strip("**")
                else:
                    q["question"] = line
                continue

            # Detect options (A), B), etc.)
            if re.match(r"^[A-D]\)\s*", line):
                q["options"].append(line)
                in_options = True
                continue

            # Detect answer line (case-insensitive)
            if re.match(r"(?i)^(\*\*)?answer:(\*\*)?\s*", line):
                answer_text = re.split(r"(?i)^(\*\*)?answer:(\*\*)?\s*", line, 1)[-1].strip()
                # Remove ** markers if they exist
                if answer_text.startswith("**") and answer_text.endswith("**"):
                    answer_text = answer_text.strip("**").strip()
                # Only update the answer if we haven't already set it (to handle duplicates)
                if not q["answer"]:
                    q["answer"] = answer_text
                else:
                    print(f"Debug: Found duplicate answer in section, keeping last: {answer_text}")
                in_options = False
                continue

            # Detect explanation line (case-insensitive)
            if re.match(r"(?i)^(\*\*)?explanation:(\*\*)?\s*", line):
                explanation_text = re.split(r"(?i)^(\*\*)?explanation:(\*\*)?\s*", line, 1)[-1].strip()
                # Remove ** markers if they exist
                if explanation_text.startswith("**") and explanation_text.endswith("**"):
                    explanation_text = explanation_text.strip("**").strip()
                q["explanation"] = explanation_text
                in_options = False
                in_explanation = True
                continue

            # If we're in explanation, append to it
            if in_explanation:
                q["explanation"] += " " + line
                continue

            # If we're in options, skip (already handled)
            if in_options:
                continue

        # Only add the question if it has question text
        if q["question"]:
            # Clean up answer (e.g., if it's "C", convert to the full option text)
            if q["answer"] and q["options"] and len(q["answer"]) == 1 and q["answer"] in "ABCD":
                for opt in q["options"]:
                    if opt.startswith(q["answer"] + ")"):
                        q["answer"] = opt
                        break
            print(f"Debug: Parsed question: {q}")
            questions.append(q)
        else:
            print(f"Debug: Skipped section, no question text found: {section[:100]}...")

    print(f"Debug: Final questions list: {questions}")
    return questions

@app.route("/")
def index():
    """Render the main SparkQuiz HTML page."""
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def quiz_api():
    """Receive quiz parameters from the frontend, generate the quiz, and return as JSON."""
    try:
        parameters = request.json
        quiz = generate_quiz(parameters)
        return jsonify({"quiz": quiz})
    except Exception as e:
        print(f"Error in quiz_api: {str(e)}")
        return jsonify({
            "quiz": [{
                "question": "Error: Server error occurred.",
                "options": [],
                "answer": "",
                "explanation": f"An unexpected error occurred on the server: {str(e)}",
                "type": ""
            }]
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
