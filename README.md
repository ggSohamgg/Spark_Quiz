# 🌟 SparkQuiz

**SparkQuiz** is an AI-powered web application that generates custom quizzes on any subject, tailored to your preferences. Built with **Flask** and styled with modern **CSS**, it leverages a large language model (LLM) to create high-quality, accurate quizzes with options for question types, difficulty levels, sub-topics, and more.

---

## ✨ Features

- **Generate quizzes** on any topic with customizable **difficulty levels** (easy, medium, hard).
- Choose from **predefined question types** (Multiple Choice, Short Answer, True/False) or add **custom types** (e.g., Fill-in-the-blank, Essay).
- Advanced options for **sub-topics**, **audience**, **language**, and **maximum question length**.
- Option to include **explanations** for deeper learning.
- **Modern, responsive UI** with glassmorphism design and animated effects.

---

## 🚀 Try SparkQuiz

Experience SparkQuiz in action!  
🔗 **[SparkQuiz on Railway](https://sparkquiz-production.up.railway.app/)** | 🔗 **[SparkQuiz on Hugging Face](https://huggingface.co/spaces/nnsohamnn/Spark_Quiz)**

---

## 🤖 LLM API/Library Used

SparkQuiz uses the **Gemini 2.5 Flash** model via the **Google Generative AI SDK**. Gemini Flash is designed for real-time applications with **low latency** and **strong reasoning** capabilities, making it ideal for interactive quiz generation.

- Model: Gemini 2.5 Flash  
- Provider: Google Generative AI  
- Library: `google.generativeai` Python SDK to make API calls

### Why Gemini 2.5 Flash?

- **Low Latency**: Optimized for fast inference times and interactive experiences like quizzes.
- **High Accuracy**: Delivers high-quality, structured outputs across diverse knowledge domains.
- **Scalable**: Works well under usage limits and supports efficient testing with low timeout risks.
- **Strong Reasoning**: Despite being lightweight, Flash retains Gemini's logical reasoning ability to generate meaningful questions and explanations.

---

## 📝 Examples of Interacting with SparkQuiz

### Example 1: Basic Quiz Generation

**Input:**
- Topic: `"Quantum Physics"`
- Difficulty: Medium
- Question Types: Multiple Choice (3 questions), Short Answer (2 questions)
- Include Explanations: Yes

**Output (displayed in the browser):**
```
# Quantum Physics Quiz

## Multiple Choice Questions

1. What is the primary source of wave-particle duality in quantum mechanics?
   - A) Heisenberg Uncertainty Principle
   - B) Schrödinger Equation
   - C) Planck's Constant
   - D) Einstein's Theory of Relativity  
   **Answer**: A) Heisenberg Uncertainty Principle  
   **Explanation**: The Heisenberg Uncertainty Principle highlights the dual nature of particles, showing that we cannot measure both position and momentum precisely at the same time.

2. Which experiment best demonstrates the quantum superposition principle?
   - A) Double-Slit Experiment
   - B) Michelson-Morley Experiment
   - C) Photoelectric Effect
   - D) Stern-Gerlach Experiment  
   **Answer**: A) Double-Slit Experiment  
   **Explanation**: The Double-Slit Experiment shows that particles like electrons exhibit both wave-like and particle-like behavior, existing in superposition until measured.

3. What does the term "quantum entanglement" refer to?
   - A) The collapse of a wave function
   - B) A correlation between two or more particles' states
   - C) The tunneling of particles through barriers
   - D) The emission of photons  
   **Answer**: B) A correlation between two or more particles' states  
   **Explanation**: Quantum entanglement means that the state of one particle is directly related to the state of another, no matter the distance between them.

## Short Answer Questions

1. Explain the significance of the Schrödinger Equation in quantum mechanics.  
   **Answer**: The Schrödinger Equation describes how the quantum state of a physical system changes over time, allowing us to predict the behavior of particles at the quantum level.

2. What is the role of the observer in the Copenhagen interpretation of quantum mechanics?  
   **Answer**: In the Copenhagen interpretation, the observer plays a critical role by causing the collapse of the wave function, determining the state of a quantum system upon measurement.

---

### Example 2: Custom Question Types

**Input:**
- Topic: `"World History"`
- Difficulty: Hard
- Question Types: True/False (2 questions), Custom: `"Essay"` (1 question)
- Sub-topics: `"World War II, Cold War"`
- Include Explanations: No

**Output:**

# World History Quiz

## True/False Questions

1. The Manhattan Project was a joint effort between the United States and the Soviet Union during World War II.  
   **Answer**: False

2. The Cuban Missile Crisis was a direct confrontation between the United States and the Soviet Union during the Cold War.  
   **Answer**: True

## Essay Questions

1. Discuss the impact of the Cold War on global politics and its lasting effects on international relations.
```
---

## 🛠️ Prompt Engineering Strategies

To ensure high-quality quiz generation, I employed the following prompt engineering strategies:

### Structured Prompts:
Used a clear, structured prompt format to instruct the LLM to generate quizzes in Markdown format. For example:

> Generate a quiz on {topic} with difficulty {difficulty}. Include the following question types: {question_types}. For each type, generate the specified number of questions: {type_counts}. Include sub-topics: {subtopics}, keywords: {keywords}, audience: {audience}, language: {language}, max length per question: {max_length}. {include_explanations ? "Include explanations for each question." : "Do not include explanations."} Format the output in Markdown with headings for each question type.

This ensures the LLM understands the exact structure and requirements, reducing ambiguity.

### Few-Shot Examples:
Provided the LLM with examples of desired quiz formats (e.g., a sample Multiple Choice question with options, answer, and explanation) to guide its output style.

### Iterative Refinement:
Initially, the LLM generated inconsistent formats (e.g., plain text instead of Markdown). I refined the prompt by explicitly requesting Markdown formatting and specifying the structure (e.g., `# Heading`, `- List items for options`).

### Parameter Constraints:
Added constraints like `max_length` per question to prevent overly verbose outputs, and enforced a maximum of 10 questions per type to manage API response times.

### Error Handling:
Included fallback messages in the prompt, instructing the LLM to return an error message if it couldn’t generate the quiz (e.g., due to invalid input), which the frontend then displays to the user.

---

### Challenges

- **Frontend Parsing**: The LLM sometimes returned inconsistent Markdown formats. I addressed this by writing a robust `parseMarkdown` function in `index.html` to handle variations (e.g., headings, bold text, lists).
- **Custom Question Types**: Allowing users to add custom question types required dynamic DOM manipulation. I implemented JavaScript to dynamically create checkboxes and quantity inputs, with a limit of 10 custom types to prevent overload.
- **Responsive Design**: Ensured the UI is responsive across devices by using CSS media queries and a grid-based layout, with glassmorphism effects for a modern look.

---

## 🧠 Acknowledgments

- Powered by **Google Generative AI** and **Gemini 2.5 Flash**.
- Fonts: **Inter** and **Montserrat** via Google Fonts.
- Deployed on **Railway** and **Glitch** – platforms that simplify app deployment and infrastructure management.
