from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen3-30b-a3b:free"

def generate_quiz(parameters):
    """
    Build the prompt from user parameters, send to OpenRouter API,
    and return the raw response text from the model in Markdown format.
    """
    # Validate that at least one question is requested
    total_questions = sum(parameters['type_counts'].get(t, 0) for t in parameters['question_types'])
    if total_questions <= 0:
        return {
            "quiz_text": "Error: Please request at least one question.\n\nNo questions were requested. Please select at least one question type with a quantity greater than 0."
        }

    # Check if API key is set
    if not OPENROUTER_API_KEY:
        return {
            "quiz_text": "Error: API key not configured.\n\nThe OPENROUTER_API_KEY environment variable is not set. Please configure it to use the OpenRouter API."
        }

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
        "Please format the quiz in Markdown as follows:\n"
        "1. Start with a heading like # Topic Quiz\n"
        "2. For each question, use a subheading like ## Question X: Type (e.g., ## Question 1: Multiple Choice)\n"
        "3. For multiple choice questions, label options as - A), - B), - C), - D)\n"
        "4. For other question types (e.g., Short Answer, True/False, or custom types like Fill-in-the-blank), present the question clearly and provide the answer format expected (e.g., for Short Answer, provide a brief sentence; for True/False, state True or False; for custom types, follow a similar clear format).\n"
        "5. If explanations are requested, include them after each question in a paragraph starting with **Explanation:**\n"
        "6. Make sure all information is factually correct\n"
        "7. Ensure each question's answer matches its explanation, and place the explanation after the answer.\n"
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
        # Timeout set to 25 seconds to fail before Gunicorn's 60-second timeout
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        data = response.json()
        quiz_text = data["choices"][0]["message"]["content"]
        print(f"Raw API Response: {quiz_text}")  # Debug: Log the raw response

        if not quiz_text or not quiz_text.strip():
            return {
                "quiz_text": "Error: No quiz content generated.\n\nThe API returned an empty response. This might be due to rate limits (10 requests/min, 50/day) or an unexpected response format."
            }

        return {
            "quiz_text": quiz_text
        }
    except requests.exceptions.Timeout:
        print("Error: OpenRouter API request timed out after 25 seconds.")
        return {
            "quiz_text": "Error: API request timed out.\n\nThe request to the OpenRouter API timed out after 25 seconds. This might be due to network issues or the API being slow to respond. Please try again later."
        }
    except requests.exceptions.RequestException as e:
        print(f"Error: OpenRouter API request failed: {str(e)}")
        return {
            "quiz_text": f"Error: API request failed.\n\nThe request to the OpenRouter API failed: {str(e)}. Please check your network connection or try again later."
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz_endpoint():
    parameters = request.get_json()
    result = generate_quiz(parameters)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
