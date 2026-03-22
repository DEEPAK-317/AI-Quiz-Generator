// DOM Elements
const uploadArea = document.getElementById('upload-area');
const pdfInput = document.getElementById('pdf-input');
const fileName = document.getElementById('file-name');
const numQuestionsSelect = document.getElementById('num-questions');
const difficultySelect = document.getElementById('difficulty');
const generateBtn = document.getElementById('generate-btn');
const demoNotice = document.getElementById('demo-notice');

const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const loadingText = document.getElementById('loading-text');
const quizSection = document.getElementById('quiz-section');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');

const quizDifficulty = document.getElementById('quiz-difficulty');
const quizProgress = document.getElementById('quiz-progress');
const progressFill = document.getElementById('progress-fill');
const quizContainer = document.getElementById('quiz-container');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const submitBtn = document.getElementById('submit-btn');

const scoreValue = document.getElementById('score-value');
const scoreText = document.getElementById('score-text');
const resultsContainer = document.getElementById('results-container');
const retryBtn = document.getElementById('retry-btn');
const newQuizBtn = document.getElementById('new-quiz-btn');

const errorMessage = document.getElementById('error-message');
const errorDismiss = document.getElementById('error-dismiss');

// State
let selectedFile = null;
let quizData = [];
let currentQuestion = 0;
let userAnswers = {};
let isDemoMode = false;

// Event Listeners
uploadArea.addEventListener('click', () => pdfInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleFileSelect(files[0]);
    }
});

pdfInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

generateBtn.addEventListener('click', generateQuiz);
prevBtn.addEventListener('click', showPreviousQuestion);
nextBtn.addEventListener('click', showNextQuestion);
submitBtn.addEventListener('click', submitQuiz);
retryBtn.addEventListener('click', retryQuiz);
newQuizBtn.addEventListener('click', resetToUpload);
errorDismiss.addEventListener('click', resetToUpload);

// Functions
function handleFileSelect(file) {
    // Block files larger than 4 MB before hitting Vercel's limit
    const MAX_SIZE_MB = 4;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        showError(`PDF is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Please upload a PDF smaller than ${MAX_SIZE_MB} MB.`);
        return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    uploadArea.classList.add('has-file');
    generateBtn.disabled = false;
}

function showSection(section) {
    [uploadSection, loadingSection, quizSection, resultsSection, errorSection].forEach(s => {
        s.hidden = true;
    });
    section.hidden = false;
}

function showLoading(message = 'Analyzing PDF content...') {
    showSection(loadingSection);
    loadingText.textContent = message;
}

function showError(message) {
    showSection(errorSection);
    errorMessage.textContent = message;
}

async function generateQuiz() {
    if (!selectedFile) return;

    const numQuestions = numQuestionsSelect.value;
    const difficulty = difficultySelect.value;

    generateBtn.disabled = true;
    generateBtn.querySelector('.btn-text').hidden = true;
    generateBtn.querySelector('.btn-loader').hidden = false;

    showLoading('Uploading PDF...');

    const formData = new FormData();
    formData.append('pdf', selectedFile);
    formData.append('num_questions', numQuestions);
    formData.append('difficulty', difficulty);

    try {
        showLoading('Analyzing PDF content...');

        const response = await fetch('/api/generate-quiz', {
            method: 'POST',
            body: formData
        });

        showLoading('Generating questions...');

        // Safely parse — Vercel can return plain text (e.g. "Request Entity Too Large")
        // which breaks response.json() and causes "Unexpected token R" error
        const contentType = response.headers.get('content-type') || '';
        let data;
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            if (response.status === 413 || text.toLowerCase().includes('too large') || text.toLowerCase().includes('entity')) {
                throw new Error('PDF is too large for the server. Please upload a smaller PDF (under 4 MB).');
            }
            throw new Error(text || `Server error (${response.status}). Please try again.`);
        }

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate quiz');
        }

        if (data.demo_mode) {
            isDemoMode = true;
            demoNotice.hidden = false;
        }

        quizData = data.questions;
        currentQuestion = 0;
        userAnswers = {};

        startQuiz(difficulty);

    } catch (error) {
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.querySelector('.btn-text').hidden = false;
        generateBtn.querySelector('.btn-loader').hidden = true;
    }
}

function startQuiz(difficulty) {
    showSection(quizSection);
    quizDifficulty.textContent = difficulty;
    quizDifficulty.className = `badge ${difficulty}`;
    renderQuestion();
    updateNavigation();
}

function renderQuestion() {
    const question = quizData[currentQuestion];
    const letters = ['A', 'B', 'C', 'D'];

    quizContainer.innerHTML = `
        <div class="question-card">
            <div class="question-number">Question ${currentQuestion + 1} of ${quizData.length}</div>
            <div class="question-text">${question.question}</div>
            <div class="options-list">
                ${question.options.map((option, index) => `
                    <div class="option-item ${userAnswers[currentQuestion] === letters[index] ? 'selected' : ''}" 
                         data-index="${index}" data-letter="${letters[index]}">
                        <span class="option-letter">${letters[index]}</span>
                        <span class="option-text">${option}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    // Add click handlers to options
    quizContainer.querySelectorAll('.option-item').forEach(option => {
        option.addEventListener('click', () => selectOption(option));
    });

    updateProgress();
}

function selectOption(optionEl) {
    const letter = optionEl.dataset.letter;
    userAnswers[currentQuestion] = letter;

    // Update UI
    quizContainer.querySelectorAll('.option-item').forEach(opt => {
        opt.classList.remove('selected');
    });
    optionEl.classList.add('selected');
}

function updateProgress() {
    const progress = ((currentQuestion + 1) / quizData.length) * 100;
    progressFill.style.width = `${progress}%`;
    quizProgress.textContent = `Question ${currentQuestion + 1} of ${quizData.length}`;
}

function updateNavigation() {
    prevBtn.disabled = currentQuestion === 0;
    
    if (currentQuestion === quizData.length - 1) {
        nextBtn.hidden = true;
        submitBtn.hidden = false;
    } else {
        nextBtn.hidden = false;
        submitBtn.hidden = true;
    }
}

function showPreviousQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        renderQuestion();
        updateNavigation();
    }
}

function showNextQuestion() {
    if (currentQuestion < quizData.length - 1) {
        currentQuestion++;
        renderQuestion();
        updateNavigation();
    }
}

function submitQuiz() {
    showResults();
}

function showResults() {
    showSection(resultsSection);

    let correctCount = 0;
    quizData.forEach((question, index) => {
        if (userAnswers[index] === question.answer) {
            correctCount++;
        }
    });

    const percentage = Math.round((correctCount / quizData.length) * 100);
    scoreValue.textContent = `${percentage}%`;
    scoreText.textContent = `${correctCount} out of ${quizData.length} correct`;

    resultsContainer.innerHTML = quizData.map((question, index) => {
        const userAnswer = userAnswers[index];
        const isCorrect = userAnswer === question.answer;
        const optionLetters = ['A', 'B', 'C', 'D'];

        return `
            <div class="result-item ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="result-question">${index + 1}. ${question.question}</div>
                <div class="result-your-answer">
                    Your answer: ${userAnswer ? `${userAnswer}. ${question.options[optionLetters.indexOf(userAnswer)] || 'Not answered'}` : 'Not answered'}
                </div>
                <div class="result-correct-answer">
                    Correct answer: ${question.answer}. ${question.options[optionLetters.indexOf(question.answer)]}
                </div>
                <div class="result-explanation">
                    <strong>Explanation:</strong> ${question.explanation}
                </div>
            </div>
        `;
    }).join('');
}

function retryQuiz() {
    userAnswers = {};
    currentQuestion = 0;
    startQuiz(difficultySelect.value);
}

function resetToUpload() {
    selectedFile = null;
    pdfInput.value = '';
    fileName.textContent = 'Supported format: PDF';
    uploadArea.classList.remove('has-file');
    generateBtn.disabled = true;
    demoNotice.hidden = true;
    isDemoMode = false;
    quizData = [];
    userAnswers = {};
    currentQuestion = 0;
    showSection(uploadSection);
}
