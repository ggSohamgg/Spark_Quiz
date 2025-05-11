import os
import json
import requests
import traceback
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5:72b-instruct"  # A capable model for quiz generation

def generate_quiz(parameters):
    """
    Build the prompt from user parameters, send to OpenRouter API,
    and return the raw response from the model without any formatting or parsing.
    """
    # Validate that at least one question is requested
    total_questions = sum(parameters['type_counts'].get(t, 0) for t in parameters['question_types'])
    if total_questions <= 0:
        return "Error: Please request at least one question. No questions were requested. Please select at least one question type with a quantity greater than 0."

    # Check if API key is set
    if not OPENROUTER_API_KEY:
        return "Error: API key not configured. The OPENROUTER_API_KEY environment variable is not set. Please configure it to use the OpenRouter API."

    # Create a much stronger prompt that explicitly requires proper formatting
    prompt = (
        "You are a specialized quiz generation API that MUST return properly formatted content. "
        "I need you to generate a quiz with specific formatting requirements. "
        "Your response MUST be properly formatted text (NOT JSON) that follows the exact structure specified below.\n\n"
        "For long responses DO NOT RETURN JSON Only FORMATTED TEXT NO JSON ANYHOW\n"
    )
    
    prompt += f"Generate a quiz with the following parameters:\n"
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
    
    # CRITICAL FORMAT INSTRUCTIONS
    prompt += (
        "\n\nCRITICAL FORMAT INSTRUCTIONS:\n"
        "Your response MUST follow this EXACT formatting structure:\n"
        "1. Start with a heading: ### Topic Quiz\n"
        "2. For each question use: #### Question X: Type\n"
        "   Example: #### Question 1: Multiple Choice\n"
        "3. For multiple choice questions, label options as A), B), C), D)\n"
        "4. Always include Answer: and Explanation: sections for each question\n"
        "5. DO NOT include any HTML, XML, or other markup languages\n"
        "6. DO NOT wrap your response in code blocks or JSON\n"
        "7. Make sure all information is factually correct\n\n"
        "8. Provide atleast 3 lines and at most 4 lines for explanation for short questions\n"
        
        "Example format for one question:\n"
        "#### Question 1: Multiple Choice\n"
        "What is the capital of France?\n"
        "A) London\n"
        "B) Berlin\n"
        "C) Paris\n"
        "D) Madrid\n"
        "Answer: C) Paris\n"
        "Explanation: Paris is the capital and largest city of France.\n\n"
        
        "YOU MUST STRICTLY FOLLOW THIS FORMAT FOR EVERY QUESTION. Do not deviate from it.\n"
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
        # Log what we're sending to the API
        print(f"Sending request to {OPENROUTER_URL} with model {MODEL}")
        print(f"Headers: {headers}")
        # Don't log the full API key if present
        safe_payload = payload.copy()
        if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 8:
            safe_headers = headers.copy()
            safe_headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY[:4]}...{OPENROUTER_API_KEY[-4:]}"
            print(f"Safe Headers: {safe_headers}")
            print(f"First 100 chars of prompt: {payload['messages'][0]['content'][:100]}...")
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=180)
        
        # Log the response status and headers for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response first 200 chars: {response.text[:200]}")
        
        # Check for HTTP errors first
        response.raise_for_status()
        
        # Try to parse as JSON - handle non-JSON responses
        try:
            data = response.json()
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")
            print(f"Response content: {response.text[:500]}...")  # Log the first 500 chars of response
            return f"Error: Invalid response from API. The API returned an invalid response format (not JSON). Status code: {response.status_code}. First 100 chars: {response.text[:100]}..."
        
        # Check if we got the expected JSON structure
        if "choices" not in data or not data["choices"] or "message" not in data["choices"][0]:
            print(f"Unexpected API response structure: {data}")
            return f"Error: Unexpected API response format. The API response did not contain the expected data structure. Received: {json.dumps(data)[:200]}..."
        
        quiz_text = data["choices"][0]["message"]["content"]
        print(f"Raw API Response: {quiz_text}")  # Debug: Log the raw response
        
        # Return the raw quiz text directly
        return quiz_text
    except requests.exceptions.RequestException as e:
        print(f"Error from OpenRouter API: {e}")
        print(f"Request exception details: {traceback.format_exc()}")
        return f"Error: Failed to generate quiz. API request failed: {str(e)}. This might be due to rate limits (10 requests/min, 50/day) or an invalid API key."
    except Exception as e:
        print(f"Unexpected error in generate_quiz: {e}")
        print(f"Exception details: {traceback.format_exc()}")
        return f"Error: Internal server error. An unexpected error occurred: {str(e)}"

@app.route('/generate_quiz', methods=['POST'])
def api_generate_quiz():
    """
    API endpoint to generate a quiz based on user parameters.
    Returns the raw output from the model as plain text.
    """
    data = request.get_json()
    if not data or 'topic' not in data or not data['topic']:
        return jsonify({"error": "Missing or empty 'topic' parameter"}), 400
    
    # Extract parameters with defaults
    parameters = {
        "topic": data.get("topic", ""),
        "difficulty": data.get("difficulty", "medium"),
        "question_types": data.get("question_types", ["Multiple Choice"]),
        "type_counts": data.get("type_counts", {"Multiple Choice":
