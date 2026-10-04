# AI Career Operating System (v2)
### AI Career Mentor, Learning Planner & Adaptive Mock Interview Platform

> **Fundamentals of Artificial Intelligence (FAI) Capstone Project**  
> An autonomous, closed-loop AI career platform built with **Python**, **Flask**, **Google Gemini AI**, and **Bayesian Knowledge Tracing**.

---

## 📌 1. Project Overview

Preparing for technical campus placements and software engineering careers requires continuous calibration across foundational knowledge, practical implementation, and interview communication.

This project upgrades a single-mode mock interviewer into a complete **AI Career Operating System** powered by three cooperating agents:

1. **AI Career Mentor**: Observes who the student is, maps target careers into canonical skill graphs, computes mathematical skill gaps, and analyzes resumes with ATS scoring and XYZ-formula rewrites.
2. **AI Learning Planner**: Generates personalized phase roadmaps, creates 5-day daily action plans using SM-2 spaced repetition and Pomodoro allocations, and retrieves verified learning resources with transparent recommendation reasoning.
3. **AI Interviewer**: Runs adaptive multi-mode interviews (Technical Deep Dive, Honest Algorithmic Code Review, and STAR-grounded HR interviews) with turn-by-turn knowledge tracing updates.

---

## 🔄 2. The Closed Feedback Loop Architecture

The platform operates as a continuous, closed feedback loop:

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
▼                                                                        │
OBSERVE ──► ANALYZE ──► PLAN ──► RECOMMEND ──► TEACH ──► TEST ──► EVALUATE ──► ADAPT ──┤
```

| Phase | Agent Role | Implementation & Operation | User Impact |
| :--- | :--- | :--- | :--- |
| **OBSERVE** | Mentor | Collects profile, self-rated skills, resume text, MCQ responses, and interview turns. | Eliminates blank-slate setup; adapts to user reality. |
| **ANALYZE** | Mentor | Computes Bayesian skill mastery, detects exact skill gaps vs. career benchmarks. | Pinpoints weak areas with zero random numbers. |
| **PLAN** | Planner | Generates multi-phase roadmap and SM-2 daily action tasks based on study hours. | Replaces guessing with structured daily momentum. |
| **RECOMMEND**| Planner | Multi-factor ranking: `w_gap + w_prereq + w_level + w_cost + w_qual + career_boost`. | Surfaces verified, real learning resources with explanations. |
| **TEACH** | Advisor | Conversational AI advisor with profile grounding and cited learning resource IDs. | Answers career questions with context-aware advice. |
| **TEST** | Interviewer| Delivers adaptive technical turns, coding challenges, and HR STAR questions. | Tests actual competence under timed pressure. |
| **EVALUATE** | Interviewer| Evaluates responses against rubrics; generates model answers; checks code logic. | Delivers immediate, rubric-grounded score out of 10. |
| **ADAPT** | System | Bayesian Knowledge Tracing updates skill mastery; recalibrates Career Readiness. | Dynamically re-plans roadmaps and adjusts next difficulty. |

---

## 🧠 3. AI Concepts Demonstrated

This system directly implements and demonstrates fundamental Artificial Intelligence principles:

| AI Concept / Technique | Implementation Location | Practical Purpose & Behavior |
| :--- | :--- | :--- |
| **Bayesian Knowledge Tracing (BKT) / EMA** | `core/services/mastery.py` | Updates latent skill mastery from evidence: `mastery_new = mastery_old + alpha * (score - mastery_old) * diff_weight`. |
| **Ebbinghaus Forgetting Curve** | `core/services/mastery.py` | Simulates exponential memory decay over time when a student neglects practicing a skill. |
| **Knowledge Graph & Prerequisite Gating**| `data/skills.json`, `core/services/mastery.py` | Directed acyclic graph ensuring advanced topics (e.g. Deep Learning) require foundational mastery (e.g. Python, ML). |
| **Supervised Multi-Criteria Recommender** | `core/services/recommender.py` | Transparent mathematical ranking combining gap priority, level fit, cost, and source authority. |
| **Structured Output Guardrails** | `ai/validator.py`, `ai/schemas.py` | Enforces JSON schema conformance, cleans code fences, and validates required response keys. |
| **Anti-Hallucination Discarder** | `ai/validator.py` | Discards any resource ID hallucinated by the LLM that does not exist in `data/resources.json`. |
| **Explainable AI (XAI) & Tracing** | `ai/trace.py`, `/trace` | Records latency, prompt version, raw LLM tokens, and validated outputs in an inspectable trace modal. |
| **Prompt Template Versioning & Caching** | `ai/prompts/*.v1.txt`, `ai/cache.py` | SHA-256 prompt hashing with TTL in-memory caching to eliminate redundant LLM calls and reduce latency. |
| **Multi-Component Readiness Index** | `core/services/readiness.py` | Weighted composite score with automatic weight re-normalization when components are unmeasured. |

---

## 💼 4. Supported Career Tracks

1. **Software Development Engineer (SDE / SWE)**: DSA, OOP, DBMS, OS, Computer Networks, System Design.
2. **Machine Learning & AI Engineer**: Python, Statistics, Classical ML, Deep Learning, Model Deployment.
3. **Full-Stack Web Developer**: JavaScript, Web Frontend (DOM/APIs), Python/Node APIs, Relational DBs.
4. **Data Scientist**: Python, Applied Statistics, Data Analysis, SQL, Classical ML.
5. **Embedded Systems & IoT Engineer**: C++, Embedded C, Microcontrollers, RTOS, Operating Systems.
6. **Cloud & DevOps Engineer**: Linux/OS, Computer Networks, Cloud Platforms, Docker/Containers, CI/CD.
7. **Cybersecurity Analyst**: Networks, System Hardening, Threat Analysis, Web Security (OWASP).
8. **Custom Niche Career**: Free-text career role dynamically decomposed into skills via Gemini AI.

---

## 🛠️ 5. Project Architecture & Layered Design

```
FAI_AI_Interview_Agent/
├── ai/                      # AI Engineering Layer
│   ├── client.py            # Encapsulated Gemini client + simulation mode
│   ├── schemas.py           # Strict JSON output schemas
│   ├── validator.py         # Anti-hallucination filter & JSON schema cleaner
│   ├── cache.py             # SHA-256 TTL prompt caching
│   ├── trace.py             # Live explainability & inspector recorder
│   └── prompts/             # Versioned prompt templates (.v1.txt)
├── core/                    # Core Business Logic (DB-Ready without DB)
│   ├── models.py            # Pure dataclasses mapping 1:1 to database tables
│   ├── repositories/        # Session & JSON data repository layer
│   └── services/            # Pure Python business services (No Flask imports)
│       ├── mastery.py       # Bayesian knowledge tracing & forgetting decay
│       ├── assessment.py    # Deterministic diagnostic scoring
│       ├── roadmap.py       # Adaptive phase timelines & switch diffs
│       ├── recommender.py   # Hybrid multi-criteria resource ranker
│       ├── planner.py       # SM-2 spaced scheduler & Pomodoro blocks
│       ├── interview.py     # Adaptive question generator & topic selection
│       ├── evaluator.py     # Technical & coding answer evaluation
│       ├── resume.py        # PDF/DOCX parsing, ATS scoring, XYZ rewrites
│       └── readiness.py     # Multi-component Career Readiness Index
├── data/                    # Canonical Ground-Truth Datasets
│   ├── careers.json         # 7 Canonical careers + roadmap templates
│   ├── skills.json          # 19 Skills knowledge graph with prerequisites
│   ├── resources.json       # 42 Real, verified learning resources
│   ├── projects.json        # 4 Portfolio projects with architectural milestones
│   ├── certifications.json  # 5 Categorized credentials (Official vs Courses)
│   ├── question_bank.json   # Diagnostic MCQs & seed interview questions
│   └── rubrics.json         # Technical & behavioral evaluation rubrics
├── routes/                  # Flask Blueprints
│   ├── main.py              # Dashboard, Advisor, Search, Settings, Trace
│   ├── onboarding.py        # Candidate registration wizard
│   ├── assessment.py        # Diagnostic assessment & calibration
│   ├── roadmap.py           # Interactive learning roadmap
│   ├── resources.py         # Verified resource library & bookmarks
│   ├── interview.py         # Multi-mode interview suite & legacy routes
│   ├── resume.py            # Resume upload & ATS screen
│   ├── planner.py           # Daily action plan & task toggling
│   ├── performance.py       # Readiness radar & interview comparison
│   └── projects_certs.py    # Portfolio projects & certifications
├── templates/               # Jinja2 Templates (Base + 18 Views)
├── static/                  # Vanilla CSS Design System (Theme-aware)
├── tests/                   # Automated pytest suite (12 tests)
└── scripts/                 # Persona regression generator & validator
```

---

## 🚀 6. Getting Started & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Internet connection (Optional; runs in **Offline Simulation Mode** if no API key is provided)

### 1. Clone & Navigate to Project
```bash
cd FAI_AI_Interview_Agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Dependencies: Flask, google-genai, python-dotenv, pypdf, python-docx, pytest)*

### 3. Configure Environment
Create a `.env` file in the root directory (or use `.env.example`):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=college_fai_project_secret_key_2026
```
> **Note**: If `GEMINI_API_KEY` is omitted, the system automatically falls back to **Offline Simulation Mode** with realistic evaluation heuristics, ensuring the application always works for grading and evaluation.

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000/`** or **`http://127.0.0.1:5000/dashboard`**

---

## 🧪 7. Running the Automated Test Suites

The project features comprehensive test suites validating math formulas, backward compatibility, data integrity, and persona divergence:

### Run the Complete v2 pytest Suite (12 Tests)
```bash
python -m pytest -v tests/test_v2_system.py
```

### Run the Persona Regression Suite (5 Personas)
```bash
python scripts/seed_demo_students.py
```
*(Outputs the comparison table proving distinct roadmap hours and divergent resource recommendations)*

### Run the Legacy Backward Compatibility Suite
```bash
python -m unittest test_interview_agent.py
```

### Validate Canonical Datasets
```bash
python scripts/validate_resources.py
```

---

## 🎓 8. College Project Evaluation Highlights

For faculty and viva evaluators, this project demonstrates:
1. **No Fake AI**: Skill mastery uses Bayesian Knowledge Tracing with difficulty weighting; readiness uses transparent mathematical formulas with weight re-normalization.
2. **Anti-Hallucination Guarantee**: Every recommended resource is verified and citations must match canonical `data/resources.json` records.
3. **Honest Review Labeling**: The coding room states explicitly: *"AI code review. Code was reviewed for complexity and edge cases, not executed in a sandbox."*
4. **Complete Backward Compatibility**: All legacy routes (`/start-interview`, `/interview`, `/evaluate`, `/next-question`, `/final-result`, `/reset`, `/api/status`) remain fully functional.
