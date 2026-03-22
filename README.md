# AI Quiz Generator 🎯

**AI Quiz Generator** is a Flask-based web application that automatically generates multiple-choice quizzes from uploaded PDF files using AI. It integrates with OpenRouter to power AI-generated questions and provides a seamless quiz experience with scoring and explanations.

---

## 🚀 Features

- 📄 Upload any PDF and instantly generate a quiz from its content
- 🔢 Choose how many questions to generate
- 🎯 Select difficulty level (Easy / Medium / Hard)
- 🤖 AI-powered question generation using OpenRouter API
- 🔄 Demo mode fallback when no API key is configured
- ✅ Interactive quiz UI with real-time scoring and answer explanations

---

## 🛠️ Tech Stack

| Layer      | Technology                     |
|------------|-------------------------------|
| Backend    | Python, Flask, Flask-CORS      |
| PDF Parser | PyPDF2                        |
| AI API     | OpenRouter (AI model gateway)  |
| Frontend   | HTML, CSS, JavaScript          |

---

## ⚡ Getting Started

### Prerequisites

- Python 3.10+
- An [OpenRouter API key](https://openrouter.ai/) *(optional — app works in demo mode without it)*

### 1. Clone the Repository

```bash
git clone https://github.com/DEEPAK-317/AI-Quiz-Generator.git
cd AI-Quiz-Generator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> If no key is provided, the app runs in **demo mode** with sample questions.

### 4. Run the App

```bash
python app.py
```

Then open your browser at:

```
http://localhost:5000
```

---

## 📁 Project Structure

```
AI-Quiz-Generator/
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not committed)
├── static/
│   ├── script.js        # Frontend JavaScript logic
│   └── style.css        # Styling
└── templates/
    └── index.html       # Main HTML page
```

---

## 📝 Notes

- Uploaded PDFs are processed **locally** by the Flask app — nothing is stored.
- The OpenRouter API is only called when a valid API key is configured.
- Best results are achieved with **text-heavy, well-structured PDFs**.

---

## 👨‍💻 Author

Made with ❤️ by [DEEPAK-317](https://github.com/DEEPAK-317)
