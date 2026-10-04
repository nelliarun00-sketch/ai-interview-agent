# AI-Powered Interview Preparation & Evaluation Agent

> **Fundamentals of Artificial Intelligence (FAI) College Project**  
> An autonomous, adaptive AI technical interview preparation system built with **Python**, **Flask**, and **Google Gemini AI**.

---

## 📌 1. Project Overview

Preparing for technical campus placements and software engineering interviews is challenging. Most mock interview platforms present static, predetermined question banks that do not adapt to individual students.

This project implements an **AI-Powered Technical Interview Agent** that acts as an intelligent interviewer. Instead of acting like a simple question-answering chatbot, the system functions as a true **Autonomous AI Agent**:
1. It observes the student's profile (target role, skills, weak areas).
2. It generates targeted technical interview questions using Google Gemini AI.
3. It evaluates candidate answers in real time with structured JSON feedback.
4. It dynamically adapts question difficulty and targets identified technical gaps.
5. Upon completing the interview, it provides a comprehensive performance summary and a **personalized 5-day preparation roadmap**.

---

## 🧠 2. AI Agent Architecture (The Agentic Loop)

This project is built around the fundamental AI Agent reasoning loop:

```
      ┌────────────────────────────────────────────────────────┐
      │                                                        │
      ▼                                                        │
┌───────────┐      ┌───────────┐      ┌──────────┐             │
│  OBSERVE  │ ───► │  ANALYZE  │ ───► │  DECIDE  │             │
└───────────┘      └───────────┘      └──────────┘             │
      │                  │                 │                   │
  Candidate        Gemini Evaluates   Identify Weak            │
  Answer &          Answer, Score     Area & Adjust            │
   Profile             (0-10)           Difficulty             │
                                           │                   │
                                           ▼                   │
                                      ┌──────────┐             │
                                      │   ACT    │ ────────────┘
                                      └──────────┘
                                     Gemini Generates
                                     Next Adaptive Q
                                    (Focus on Weakness)
```

### Detailed Agent Breakdown:
- **OBSERVE**: The agent reads the student's background, target job role, previous question, and submitted answer.
- **ANALYZE**: The agent calls Gemini AI using structured prompt engineering to critically evaluate technical correctness, depth, and clarity.
- **DECIDE**: The agent identifies the candidate's exact technical gap (`weak_area`) and adjusts difficulty:
  - **Score 0 – 4 (Low)**: Reduces difficulty (`Hard → Medium → Easy`) or maintains `Easy`.
  - **Score 5 – 7 (Medium)**: Maintains current difficulty level.
  - **Score 8 – 10 (High)**: Increases challenge level (`Easy → Medium → Hard`).
- **ACT**: The agent formulates a new, targeted question focusing specifically on the student's identified weak area.
- **ADAPT**: The system continuously iterates through a 5-question interview loop, tracking historical score progression.

---

## ✨ 3. Key Features

- **Personalized Setup**: Calibrates questions to the student's target role (e.g., Python Developer, Data Analyst, Software Engineer).
- **Google Gemini Integration**: Utilizes the modern `google-genai` Python SDK with structured JSON output enforcement (`response_mime_type="application/json"`).
- **Multi-Factor Adaptive Questions**: Questions are generated using previous answers, scores, and detected technical gaps.
- **Structured Feedback Cards**:
  - Score out of 10
  - What the student did well (Strengths)
  - What needs improvement
  - Specific weak technical concept
  - Recommended study topic
  - Complete high-scoring model answer
- **5-Day Actionable Study Plan**: Gemini builds a day-by-day remediation plan customized to the candidate's daily study hours (e.g., 2 hours/day).
- **Fail-Safe Simulation Mode**: If an API key is not yet set or external networks are offline, built-in algorithmic simulations ensure the application remains fully testable without throwing errors.

---

## 🛠️ 4. Technologies Used

- **Backend**: Python 3.10+ & Flask (Lightweight web framework)
- **AI / LLM**: Google Gemini API via official `google-genai` SDK (`gemini-2.5-flash`)
- **Frontend**: HTML5, Vanilla CSS3 (modern glassmorphism cards, responsive flexbox/grid)
- **State Management**: Flask Secure Client Sessions
- **Environment**: `python-dotenv` for safe credential management

---

## 📁 5. Project Directory Structure

```text
FAI_AI_Interview_Agent/
│
├── app.py                     # Main Flask application and AI Agent core logic
├── .env                       # Local environment variables (API keys - not in git)
├── .env.example               # Template showing required configuration variables
├── .gitignore                 # Excludes .env, virtual environments, and caches
├── requirements.txt           # Python dependencies
├── test_interview_agent.py    # Automated end-to-end test suite
├── README.md                  # Complete documentation and presentation guide
│
├── templates/                 # Jinja2 HTML Templates
│   ├── index.html             # Candidate registration & profile setup
│   ├── interview.html         # Active technical interview question & answer form
│   ├── evaluation.html        # Real-time AI evaluation, scoring & feedback card
│   ├── next_question.html     # Adaptive question presentation with AI reasoning
│   └── result.html            # Final interview summary & 5-day personalized plan
│
└── static/                    # Frontend styling
    └── style.css              # Custom responsive stylesheet
```

---

## 🚀 6. Step-by-Step Installation & Setup

### Step 1: Open Terminal / Command Prompt
Navigate to the project root directory:
```bash
cd FAI_AI_Interview_Agent
```

### Step 2: Create a Python Virtual Environment
Creating an isolated virtual environment ensures packages do not conflict:
```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment
- **Windows (Command Prompt / PowerShell)**:
  ```powershell
  venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### Step 4: Install Dependencies
Install all required libraries using pip:
```bash
pip install -r requirements.txt
```

### Step 5: Configure Your Gemini API Key
1. Get a free Google Gemini API key at: [Google AI Studio](https://aistudio.google.com/)
2. Open the `.env` file in a text editor.
3. Paste your API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
   *(Note: The project includes a simulation fallback mode so you can test immediately even before obtaining a key!)*

---

## 🖥️ 7. Running the Application

Start the Flask server:
```bash
python app.py
```

You will see:
```text
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 8. How to Test the Project

1. **Home Page**:
   - Enter candidate details:
     - Name: `Arun`
     - Target Role: `Python Developer`
     - Current Skills: `Python, C++, SQL`
     - Initial Weak Areas: `OOP, DSA`
     - Daily Prep Time: `2 hours per day`
   - Click **Start AI Interview**.

2. **Question Answering & Evaluation**:
   - Answer Question 1 (e.g., explain OOP principles).
   - Click **Submit Answer for Evaluation**.
   - Observe the score (out of 10), strengths, improvement suggestions, and the model answer.
   - Click **Generate Next Question**.

3. **Observe Adaptation**:
   - Notice that Question 2 specifically focuses on the weak technical area identified from your previous response (e.g., Inheritance or Polymorphism).
   - If you scored high, difficulty escalates to `Hard`; if you scored lower, it adjusts to `Easy` or `Medium`.

4. **Complete 5 Questions**:
   - After Question 5, click **View Final Interview Summary**.
   - Review your Overall Score, Average Score, Performance Badge, Strong Areas, and the custom **5-Day Study Plan**.

---

## 🎓 9. College Presentation & Viva Guide

When explaining this project to professors or examiners:
1. **Explain the Difference from a Chatbot**:  
   *"A standard chatbot produces one-off responses. Our system is an Autonomous AI Agent maintaining an internal state (question history, difficulty level, weak technical areas) that continuously closes a feedback loop (Observe → Analyze → Decide → Act → Adapt)."*
2. **Explain Structured Output**:  
   *"Rather than asking the LLM to output free text and parsing it with brittle string operations, we enforce JSON schema generation via Gemini's `application/json` response mode and parse it securely."*
3. **Explain the State Machine**:  
   *"Flask sessions maintain the candidate trajectory across all 5 questions without requiring an external database, allowing lightweight deployment and complete privacy."*

---

## 🔮 10. Future Enhancements

- **Voice & Speech-to-Text**: Allowing candidates to speak their answers using Web Speech API.
- **Code Execution Sandbox**: Integrating an in-browser Python IDE to execute code answers.
- **Resume PDF Parsing**: Automatically reading candidate skills from an uploaded resume.
- **Analytics Dashboard**: Storing long-term candidate progress across multiple interview attempts with SQLite.

---

## 📄 License
Educational project developed for college coursework.
