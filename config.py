"""
Application Configuration and Constants
---------------------------------------
Central configuration module for the AI Career Operating System.
Loads environment variables safely and defines weights, defaults, and feature flags.
"""

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "fai_career_os_secret_key_v2_2026")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"


    # Gemini AI configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    AI_TIMEOUT_SECONDS = int(os.environ.get("AI_TIMEOUT_SECONDS", 15))
    AI_OFFLINE_MODE = os.environ.get("AI_OFFLINE_MODE", "0") == "1"
    AI_CACHE_TTL_SECONDS = int(os.environ.get("AI_CACHE_TTL_SECONDS", 3600))

    # Readiness Score Component Weights (Transparent & documented)
    # Sum must equal 1.0 (100%)
    READINESS_WEIGHTS = {
        "technical": 0.30,        # Mastery of target career skills
        "projects": 0.15,         # Realized portfolio & mini-projects
        "interview": 0.20,        # Cumulative mock interview evaluations
        "resume": 0.15,           # ATS check, metrics & structure score
        "communication": 0.10,    # Communication clarity from interviews
        "learning_progress": 0.10 # Completed syllabus and resources
    }

    # Recommender Weights for Resource Retrieval
    RECOMMENDER_WEIGHTS = {
        "gap_priority": 0.35,
        "prerequisite_readiness": 0.20,
        "level_fit": 0.15,
        "cost_fit": 0.10,
        "time_fit": 0.10,
        "quality": 0.10
    }

    # Knowledge Tracing / Mastery parameters
    MASTERY_ALPHA_INITIAL = 0.40  # Learning rate for first attempt
    MASTERY_DECAY_RATE_PER_DAY = 0.005 # Forgetting curve decay rate
    MIN_EVIDENCE_ATTEMPTS = 2     # Minimum attempts for high confidence
    WEAKNESS_THRESHOLD = 0.60     # Mastery below 60% flags weakness

    # Career Groups
    CAREER_GROUPS = [
        "Software Engineering",
        "Data & Analytics",
        "Artificial Intelligence & ML",
        "Cloud & DevOps",
        "Cybersecurity",
        "Embedded & IoT",
        "Product & QA"
    ]

config = Config()
