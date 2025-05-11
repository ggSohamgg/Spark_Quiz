from flask import Flask, render_template, request, jsonify
import requests
import os
import re

app = Flask(__name__)

# Get API key from environment variable
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Check if API key is available
if not OPENROUTER_API_KEY:
    print("Error: OPENROUTER_API_KEY environment variable not set.")
else:
    print("API key loaded successfully.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz_endpoint():
    if not OPENROUTER_API_KEY:
        return jsonify({
            'error': 'API key is not configured. Please contact the administrator.'
        }), 500

    data = request.get_json()
    print("Received data:", data)  # Debug log

    try:
        parameters = {
            'topic': data.get('topic', ''),
            'difficulty': data.get('difficulty', 'Medium'),
            'question_types': data.get('questionTypes', []),
            'type_counts': data.get('typeCounts', {}),
            'subtopics': data.get('subtopics', ''),
            'audience': data.get('audience', 'General'),
            'language': data.get('language', 'English'),
            'additional_instructions': data.get('additionalInstructions', '')
        }

        # Calculate total questions requested
        total_questions = sum(int(parameters['type_counts'].get(qtype, 0)) for qtype in parameters['question_types'])
        if total_questions <= 0:
            return jsonify({
                'error': 'Invalid request: No questions requested. Please select at least one question type with a count greater than 0.'
            }), 400

        questions = generate_quiz(parameters, total_questions)
        if not questions:
            return jsonify({
                'error': 'Failed to generate quiz. No questions were returned by the API. Please try again or adjust your parameters.'
            }), 500

        return jsonify({'questions': questions})
    except Exception as e:
        print(f"Error in generate_quiz_endpoint: {str(e)}")
        return jsonify({
            'error': f'Failed to generate quiz. Error: {str(e)}'
        }), 500

def generate_quiz(parameters, total_questions):
    """
    Generate quiz questions based on user parameters using OpenRouter API.
    """
    print("Generating quiz with parameters:", parameters)

    # Build the prompt for the API
    prompt = f"Generate a quiz on the topic of '{parameters['topic']}' with the following specifications:\n"
    prompt += f"Difficulty Level: {parameters['difficulty']}\n"
    prompt += "Question Types and Counts:\n"
    for qtype in parameters['question_types']:
        count = parameters['type_counts'].get(qtype, 0)
        if count > 0:
            prompt += f"- {qtype}: {count} questions\n"
    prompt += f"Ensure exactly {total_questions} questions are generated, matching the requested counts for each type.\n"
    if parameters['subtopics']:
        prompt += f"Focus on these subtopics: {parameters['subtopics']}\n"
    if parameters['audience']:
        prompt += f"Target Audience: {parameters['audience']}\n"
    if parameters['language']:
        prompt += f"Language: {parameters['language']}\n"
    if parameters['additional_instructions']:
        prompt += f"Additional Instructions: {parameters['additional_instructions']}\n"
    prompt += "\nFormat the output as follows for each question:\n"
    prompt += "#### Question X: [Type]\n"
    prompt += "Question text here\n"
    prompt += "For Multiple Choice, list options as:\nA) Option1\nB) Option2\nC) Option3\nD) Option4\n"
    prompt += "**Answer:** Correct answer here\n"
    prompt += "**Explanation:** Detailed explanation here\n\n"
    prompt += "Ensure all questions are relevant, accurate, and follow the specified format strictly."

    print("Generated prompt:", prompt)

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen-2.5-72b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant tasked with generating educational quizzes."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4096
            },
            timeout=180  # Set timeout to 180 seconds
        )

        response.raise_for_status()
        response_json = response.json()
        print("Raw API Response:", response_json)  # Debug log

        quiz_text = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not quiz_text:
            print("Error: Empty response content from API.")
            return []

        questions = parse_quiz_text(quiz_text)
        print(f"Parsed {len(questions)} questions from response.")

        # Post-parsing validation: Check if the number of questions matches the requested total
        if len(questions) < total_questions:
            print(f"Warning: Only {len(questions)} questions generated out of {total_questions} requested.")
            questions.append({
                "question": f"Warning: Incomplete Quiz ({len(questions)}/{total_questions} questions generated)",
                "options": [],
                "answer": "",
                "explanation": "The API generated fewer questions than requested. Please try again or adjust parameters.",
                "type": "Notice"
            })

        return questions
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        error_msg = str(e)
        if "429" in error_msg:
            error_msg += " (Rate limit exceeded. Note: Free tier limits are 10 requests/min, 50/day. Please try again later.)"
        elif "401" in error_msg or "403" in error_msg:
            error_msg += " (Authentication error. API key may be invalid or revoked.)"
        raise Exception(error_msg)
    except Exception as e:
        print(f"Unexpected error in generate_quiz: {str(e)}")
        raise Exception(f"Unexpected error: {str(e)}")

def parse_quiz_text(text):
    """
    Parse the quiz text response from the API into a structured list of questions.
    """
    print("Parsing quiz text content:")
    print(text)  # Debug log of raw text to parse

    # Split the text into sections based on question headings like "#### Question X: Type"
    sections = re.split(r'####\s*Question\s*\d+[:\s]*\w*', text)
    print(f"Split sections: {len(sections)} parts found")
    print("Sections:", sections)  # Debug log

    questions = []
    current_question = None
    question_number = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Try to extract the heading from the original text to determine type
        heading_match = re.search(r'####\s*Question\s*\d+[:\s]*(\w+[\w\s\/]*)\s*$', text[:text.find(section) + len(section)], re.MULTILINE)
        if heading_match:
            q_type = heading_match.group(1).strip()
            print(f"Processing section for type {q_type}: {section[:100]}...")  # Debug log
        else:
            print(f"Skipping section, no valid heading found: {section[:50]}...")  # Debug log
            continue

        lines = section.split('\n')
        current_question = {
            'question': '',
            'options': [],
            'answer': '',
            'explanation': '',
            'type': q_type
        }
        mode = 'question'
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('**Answer:**') or line.startswith('**Answer**:'):
                mode = 'answer'
                current_question['answer'] = line.replace('**Answer:**', '').replace('**Answer**:', '').strip()
            elif line.startswith('**Explanation:**') or line.startswith('**Explanation**:'):
                mode = 'explanation'
                current_question['explanation'] = line.replace('**Explanation:**', '').replace('**Explanation**:', '').strip()
            elif mode == 'question' and (line.startswith('A)') or line.startswith('a)')) and 'Multiple Choice' in q_type:
                mode = 'options'
                current_question['options'].append(line.strip())
            elif mode == 'options' and (line.startswith('B)') or line.startswith('b)') or line.startswith('C)') or line.startswith('c)') or line.startswith('D)') or line.startswith('d)')):
                current_question['options'].append(line.strip())
            elif mode == 'question':
                current_question['question'] += line + ' '
            elif mode == 'answer':
                current_question['answer'] += line + ' '
            elif mode == 'explanation':
                current_question['explanation'] += line + ' '

        # Clean up the fields
        current_question['question'] = current_question['question'].strip()
        current_question['answer'] = current_question['answer'].strip()
        current_question['explanation'] = current_question['explanation'].strip()

        # For Multiple Choice, if answer is just a letter (e.g., "C"), expand it to full option text
        if 'Multiple Choice' in q_type and current_question['answer'] and len(current_question['answer']) == 1:
            for opt in current_question['options']:
                if opt.startswith(current_question['answer'] + ')') or opt.startswith(current_question['answer'].lower() + ')'):
                    current_question['answer'] = opt
                    break

        # Only add if there's a question text
        if current_question['question']:
            questions.append(current_question)
            print(f"Parsed question: {current_question}")  # Debug log
        else:
            print(f"Skipped incomplete question for type {q_type}")

        question_number += 1

    # Fallback parsing for cases where format might be slightly off
    if not questions:
        print("No questions parsed with standard method. Attempting fallback parsing...")
        lines = text.split('\n')
        current_question = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\d+\.\s*', line) or line.lower().startswith('question'):
                if current_question and current_question.get('question'):
                    questions.append(current_question)
                current_question = {
                    'question': line,
                    'options': [],
                    'answer': '',
                    'explanation': '',
                    'type': 'Unknown'
                }
            elif current_question and (line.startswith('A)') or line.startswith('a)')):
                current_question['options'].append(line)
            elif current_question and (line.startswith('B)') or line.startswith('b)') or line.startswith('C)') or line.startswith('c)') or line.startswith('D)') or line.startswith('d)')):
                current_question['options'].append(line)
            elif current_question and 'answer' in line.lower():
                current_question['answer'] = line
            elif current_question and 'explanation' in line.lower():
                current_question['explanation'] = line
            elif current_question and current_question.get('question') and not current_question.get('answer'):
                current_question['question'] += ' ' + line
        if current_question and current_question.get('question'):
            questions.append(current_question)
            print("Fallback parsing added questions:", questions)

    print(f"Final questions list: {questions}")  # Debug log
    return questions

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
