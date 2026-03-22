from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import PyPDF2
import requests
import os
import json
import io
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Vercel has a 4.5MB request body limit — we set 4MB to stay safely below it
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB


@app.errorhandler(413)
def request_entity_too_large(error):
    """Return JSON error when uploaded file exceeds size limit"""
    return jsonify({
        "error": "PDF file is too large. Please upload a file smaller than 4 MB."
    }), 413

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def split_text_into_chunks(text, chunk_size=2000, overlap=200):
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def call_gemini(prompt):
    """Call Google Gemini API to generate questions"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None

    headers = {
        "Content-Type": "application/json",
    }

    system_instruction = "You are a quiz generation expert. Generate questions in valid JSON array format only. No markdown, no explanation."

    data = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4000,
        },
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        return content
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def build_prompt(chunk, num_questions, difficulty):
    """Build the prompt for question generation"""
    difficulty_rules = {
        "easy": "Focus on basic facts, definitions, and simple recall. Questions should test direct information from the text.",
        "medium": "Focus on concept understanding and slight reasoning. Questions should require understanding relationships between ideas.",
        "hard": "Focus on inference, application, and multi-step thinking. Questions should require analysis and critical evaluation.",
    }

    prompt = f"""Generate exactly {num_questions} {difficulty}-level multiple-choice questions from the following text.

Rules:
- {difficulty_rules.get(difficulty, difficulty_rules["medium"])}
- Each question MUST have exactly 4 options (A, B, C, D)
- Each question must have a clear correct answer
- Provide a brief explanation for the correct answer
- Return ONLY a valid JSON array, no other text

Format:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "A",
    "difficulty": "{difficulty}",
    "explanation": "Brief explanation of why this is correct"
  }}
]

Text:
{chunk}"""
    return prompt


def parse_questions_from_response(response_text):
    """Parse questions from LLM response"""
    if not response_text:
        return []

    try:
        # Try to find JSON array in the response
        response_text = response_text.strip()

        # If response starts with ```json, extract it
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        questions = json.loads(response_text)
        return questions if isinstance(questions, list) else []
    except json.JSONDecodeError:
        # Try to extract JSON array from text
        try:
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                questions = json.loads(json_str)
                return questions if isinstance(questions, list) else []
        except:
            pass
        return []


def generate_demo_questions(num_questions, difficulty):
    """Generate demo questions when API key is not available"""
    demo_questions = []

    samples = {
        "easy": [
            {
                "question": "What is the main purpose of reading comprehension?",
                "options": [
                    "To memorize text",
                    "To understand meaning",
                    "To read faster",
                    "To skip pages",
                ],
                "answer": "B",
                "explanation": "Reading comprehension focuses on understanding the meaning of text.",
            },
            {
                "question": "Which of these is a key reading skill?",
                "options": ["Skimming", "Ignoring", "Skipping", "Sleeping"],
                "answer": "A",
                "explanation": "Skimming helps quickly identify main ideas.",
            },
            {
                "question": "What helps improve vocabulary?",
                "options": [
                    "Reading widely",
                    "Avoiding books",
                    "Watching TV only",
                    "Sleeping more",
                ],
                "answer": "A",
                "explanation": "Reading widely exposes you to new words in context.",
            },
        ],
        "medium": [
            {
                "question": "How does context help in understanding unfamiliar words?",
                "options": [
                    "It doesn't help",
                    "Surrounding words provide clues",
                    "You must use a dictionary",
                    "Words have no context",
                ],
                "answer": "B",
                "explanation": "Context clues from surrounding text help infer word meanings.",
            },
            {
                "question": "What is the relationship between critical thinking and reading?",
                "options": [
                    "No relationship",
                    "Critical thinking enhances comprehension",
                    "Reading prevents thinking",
                    "They are opposites",
                ],
                "answer": "B",
                "explanation": "Critical thinking helps analyze and evaluate what you read.",
            },
            {
                "question": "Why is summarization an important reading skill?",
                "options": [
                    "It wastes time",
                    "It identifies key information",
                    "It makes reading harder",
                    "It's not important",
                ],
                "answer": "B",
                "explanation": "Summarization helps identify and retain key information.",
            },
        ],
        "hard": [
            {
                "question": "How would you evaluate the credibility of arguments presented in a text?",
                "options": [
                    "Accept all claims",
                    "Check evidence and sources",
                    "Ignore the author",
                    "Read only titles",
                ],
                "answer": "B",
                "explanation": "Evaluating evidence and sources is essential for assessing argument credibility.",
            },
            {
                "question": "What inference can be drawn when an author uses specific rhetorical devices?",
                "options": [
                    "No inference needed",
                    "Author's intent and persuasion strategy",
                    "Text has no meaning",
                    "Language is random",
                ],
                "answer": "B",
                "explanation": "Rhetorical devices reveal author's persuasive intent and communication strategy.",
            },
            {
                "question": "How does analyzing text structure contribute to deeper understanding?",
                "options": [
                    "Structure doesn't matter",
                    "Reveals organization and logical flow",
                    "Only length matters",
                    "Format is irrelevant",
                ],
                "answer": "B",
                "explanation": "Understanding text structure reveals how ideas are organized and connected.",
            },
        ],
    }

    difficulty_questions = samples.get(difficulty, samples["medium"])

    for i in range(num_questions):
        q = difficulty_questions[i % len(difficulty_questions)].copy()
        q["difficulty"] = difficulty
        demo_questions.append(q)

    return demo_questions


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    """Generate quiz from uploaded PDF"""

    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400

    pdf_file = request.files["pdf"]
    if pdf_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    num_questions = int(request.form.get("num_questions", 5))
    difficulty = request.form.get("difficulty", "medium").lower()

    if num_questions < 1 or num_questions > 50:
        return jsonify({"error": "Number of questions must be between 1 and 50"}), 400

    if difficulty not in ["easy", "medium", "hard"]:
        return jsonify({"error": "Difficulty must be easy, medium, or hard"}), 400

    try:
        text = extract_text_from_pdf(pdf_file)

        if len(text) < 100:
            return jsonify(
                {
                    "error": "PDF content is too short. Please upload a PDF with more text."
                }
            ), 400

        # Check if API key is available
        if (
            not GEMINI_API_KEY
            or GEMINI_API_KEY == "your_gemini_api_key_here"
        ):
            demo_questions = generate_demo_questions(num_questions, difficulty)
            return jsonify(
                {
                    "questions": demo_questions,
                    "demo_mode": True,
                    "message": "Running in demo mode. Add your Gemini API key to .env for real AI-generated questions.",
                }
            )

        # Split text into chunks
        chunks = split_text_into_chunks(text)

        # Distribute questions across chunks
        questions_per_chunk = max(1, num_questions // len(chunks))
        extra = num_questions % len(chunks)

        all_questions = []

        for i, chunk in enumerate(chunks):
            chunk_questions = questions_per_chunk
            if i < extra:
                chunk_questions += 1

            if len(all_questions) >= num_questions:
                break

            remaining = num_questions - len(all_questions)
            chunk_questions = min(chunk_questions, remaining)

            prompt = build_prompt(chunk, chunk_questions, difficulty)
            response = call_gemini(prompt)

            if response:
                questions = parse_questions_from_response(response)
                all_questions.extend(questions)

        # Trim to exact number
        all_questions = all_questions[:num_questions]

        # Ensure difficulty is set
        for q in all_questions:
            q["difficulty"] = difficulty

        if not all_questions:
            return jsonify(
                {"error": "Failed to generate questions. Please try again."}
            ), 500

        return jsonify(
            {
                "questions": all_questions,
                "demo_mode": False,
                "total_generated": len(all_questions),
            }
        )

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-quiz-text", methods=["POST"])
def generate_quiz_from_text():
    """Generate quiz from text extracted client-side (bypasses Vercel upload size limit)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    pdf_text = data.get("pdf_text", "").strip()
    num_questions = int(data.get("num_questions", 5))
    difficulty = data.get("difficulty", "medium").lower()

    if not pdf_text:
        return jsonify({"error": "No text provided"}), 400

    if len(pdf_text) < 100:
        return jsonify({"error": "PDF content is too short. Please upload a PDF with more text."}), 400

    if num_questions < 1 or num_questions > 50:
        return jsonify({"error": "Number of questions must be between 1 and 50"}), 400

    if difficulty not in ["easy", "medium", "hard"]:
        return jsonify({"error": "Difficulty must be easy, medium, or hard"}), 400

    try:
        # Demo mode fallback
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            demo_questions = generate_demo_questions(num_questions, difficulty)
            return jsonify({
                "questions": demo_questions,
                "demo_mode": True,
                "message": "Running in demo mode. Add your Gemini API key for real AI-generated questions.",
            })

        # Split text into chunks and generate questions
        chunks = split_text_into_chunks(pdf_text)
        questions_per_chunk = max(1, num_questions // len(chunks))
        extra = num_questions % len(chunks)
        all_questions = []

        for i, chunk in enumerate(chunks):
            chunk_questions = questions_per_chunk + (1 if i < extra else 0)
            if len(all_questions) >= num_questions:
                break
            remaining = num_questions - len(all_questions)
            chunk_questions = min(chunk_questions, remaining)

            prompt = build_prompt(chunk, chunk_questions, difficulty)
            response = call_gemini(prompt)

            if response:
                questions = parse_questions_from_response(response)
                all_questions.extend(questions)

        all_questions = all_questions[:num_questions]
        for q in all_questions:
            q["difficulty"] = difficulty

        if not all_questions:
            return jsonify({"error": "Failed to generate questions. Please try again."}), 500

        return jsonify({
            "questions": all_questions,
            "demo_mode": False,
            "total_generated": len(all_questions),
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
