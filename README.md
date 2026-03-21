# quizTool

quizTool is a Flask web app that generates multiple-choice quizzes from uploaded PDF files. It can use OpenRouter for AI-generated questions or fall back to demo questions when no API key is configured.

## Features

- Upload a PDF and generate a quiz from its content
- Choose question count and difficulty level
- AI-powered generation with OpenRouter
- Demo mode fallback when no API key is available
- Quiz review with scoring and explanations

## Tech Stack

- Python
- Flask
- Flask-CORS
- PyPDF2
- Requests
- HTML, CSS, and JavaScript

## Getting Started

### Prerequisites

- Python 3.10+
- An OpenRouter API key if you want live AI-generated questions

### Install

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

If no key is provided, the app runs in demo mode with sample questions.

### Run the App

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

## Project Structure

```text
quizTool/
├── app.py
├── requirements.txt
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    └── index.html
```

## Notes

- Uploaded PDFs are processed locally by the Flask app.
- The OpenRouter API is only used when an API key is configured.
- Large or text-light PDFs may not generate good results.
