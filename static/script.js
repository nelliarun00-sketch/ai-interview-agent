/* ==========================================================================
   AI-POWERED INTERVIEW AGENT: CLIENT INTERACTION ENGINE
   Features: Audio Speech Synthesis (TTS), Voice Dictation (STT),
             Live HUD Timer, Word Metrics, Role Presets, and Clipboard Utils.
   ========================================================================== */

// -------------------------------------------------------------
// 1. Role Preset Fillers (Home Page)
// -------------------------------------------------------------
const rolePresets = {
  python: {
    role: "Python Backend Developer",
    skills: "Python, FastAPI, Django, PostgreSQL, Redis",
    weakAreas: "OOP Principles, AsyncIO, Memory Management",
    prepTime: "2 hours per day"
  },
  ai: {
    role: "AI / Machine Learning Intern",
    skills: "Python, PyTorch, Scikit-Learn, Pandas, NumPy",
    weakAreas: "Bias-Variance Tradeoff, Attention Mechanisms, Backprop",
    prepTime: "3 hours per day"
  },
  fullstack: {
    role: "Full-Stack Software Engineer",
    skills: "JavaScript, TypeScript, React, Node.js, SQL",
    weakAreas: "System Design, Event Loop, REST API Security",
    prepTime: "2.5 hours per day"
  },
  data: {
    role: "Data Analyst & SQL Specialist",
    skills: "SQL, Python, Power BI, Excel, ETL Pipelines",
    weakAreas: "Window Functions, Database Indexing, Aggregations",
    prepTime: "1.5 hours per day"
  },
  dsa: {
    role: "Junior Software Engineer (Campus Placements)",
    skills: "C++, Java, Python, Git",
    weakAreas: "Dynamic Programming, Graph Traversals, Trees",
    prepTime: "2 hours per day"
  }
};

function applyPreset(presetKey) {
  const data = rolePresets[presetKey];
  if (!data) return;

  const roleInput = document.getElementById("job_role");
  const skillsInput = document.getElementById("skills");
  const weakInput = document.getElementById("weak_areas");
  const prepInput = document.getElementById("prep_time");

  if (roleInput) roleInput.value = data.role;
  if (skillsInput) skillsInput.value = data.skills;
  if (weakInput) weakInput.value = data.weakAreas;
  if (prepInput) prepInput.value = data.prepTime;

  // Visual feedback animation
  const formCard = document.querySelector(".card");
  if (formCard) {
    formCard.style.boxShadow = "0 0 35px rgba(99, 102, 241, 0.4)";
    setTimeout(() => {
      formCard.style.boxShadow = "";
    }, 600);
  }
}

// -------------------------------------------------------------
// 2. Audio Speech Synthesis (Text-to-Speech)
// -------------------------------------------------------------
let currentUtterance = null;

function playQuestionTTS(text, btnElement) {
  if (!('speechSynthesis' in window)) {
    alert("Audio speech synthesis is not supported in this browser.");
    return;
  }

  // If already speaking, stop it
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    if (btnElement) {
      btnElement.innerHTML = "🔊 Listen to Question";
      btnElement.classList.remove("active");
    }
    return;
  }

  const cleanText = text.replace(/[*_#`]/g, "");
  currentUtterance = new SpeechSynthesisUtterance(cleanText);
  currentUtterance.rate = 0.95;
  currentUtterance.pitch = 1.0;

  // Choose a clean English voice if available
  const voices = window.speechSynthesis.getVoices();
  const naturalVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha")));
  if (naturalVoice) {
    currentUtterance.voice = naturalVoice;
  }

  if (btnElement) {
    btnElement.innerHTML = "⏹️ Stop Audio";
    btnElement.classList.add("active");
  }

  currentUtterance.onend = () => {
    if (btnElement) {
      btnElement.innerHTML = "🔊 Listen to Question";
      btnElement.classList.remove("active");
    }
  };

  currentUtterance.onerror = () => {
    if (btnElement) {
      btnElement.innerHTML = "🔊 Listen to Question";
      btnElement.classList.remove("active");
    }
  };

  window.speechSynthesis.speak(currentUtterance);
}

// -------------------------------------------------------------
// 3. Speech-to-Text Voice Dictation (Microphone Answering)
// -------------------------------------------------------------
let recognition = null;
let isRecording = false;

function toggleVoiceDictation(textareaId, micBtnElement) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
    return;
  }

  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  if (isRecording && recognition) {
    recognition.stop();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isRecording = true;
    if (micBtnElement) {
      micBtnElement.innerHTML = "🔴 Recording... (Click to Stop)";
      micBtnElement.classList.add("active");
      micBtnElement.style.borderColor = "var(--danger)";
    }
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    textarea.value = (textarea.value.trim() ? textarea.value.trim() + " " : "") + transcript;
    updateWordMetrics(textareaId);
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    stopRecognition(micBtnElement);
  };

  recognition.onend = () => {
    stopRecognition(micBtnElement);
  };

  recognition.start();
}

function stopRecognition(micBtnElement) {
  isRecording = false;
  if (micBtnElement) {
    micBtnElement.innerHTML = "🎙️ Voice Dictation";
    micBtnElement.classList.remove("active");
    micBtnElement.style.borderColor = "";
  }
}

// -------------------------------------------------------------
// 4. Live Answer Metrics (Words, Characters, Target indicator)
// -------------------------------------------------------------
function updateWordMetrics(textareaId) {
  const textarea = document.getElementById(textareaId);
  const wordCountElem = document.getElementById("word-count-val");
  const charCountElem = document.getElementById("char-count-val");
  const statusElem = document.getElementById("answer-depth-status");

  if (!textarea) return;

  const text = textarea.value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  const chars = text.length;

  if (wordCountElem) wordCountElem.textContent = words;
  if (charCountElem) charCountElem.textContent = chars;

  if (statusElem) {
    if (words === 0) {
      statusElem.textContent = "Awaiting response";
      statusElem.className = "";
    } else if (words < 25) {
      statusElem.textContent = "Brief answer (Elaborate for higher score)";
      statusElem.className = "";
      statusElem.style.color = "var(--warning)";
    } else if (words <= 120) {
      statusElem.textContent = "✨ Great technical depth";
      statusElem.className = "good";
      statusElem.style.color = "var(--success)";
    } else {
      statusElem.textContent = "Comprehensive explanation";
      statusElem.className = "good";
      statusElem.style.color = "var(--accent-cyan)";
    }
  }
}

// Enable Tab key indentation inside textareas
function enableTabKey(textareaId) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      textarea.value = textarea.value.substring(0, start) + "    " + textarea.value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + 4;
    }
    // Allow Ctrl+Enter or Cmd+Enter to submit answer
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const form = textarea.closest("form");
      if (form) form.submit();
    }
  });
}

// -------------------------------------------------------------
// 5. Code Mode Toggle
// -------------------------------------------------------------
function toggleCodeMode(textareaId, btnElement) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  textarea.classList.toggle("code-font");
  const isCode = textarea.classList.contains("code-font");

  if (btnElement) {
    if (isCode) {
      btnElement.innerHTML = "📝 Text Mode";
      btnElement.classList.add("active");
    } else {
      btnElement.innerHTML = "{ } Code Mode";
      btnElement.classList.remove("active");
    }
  }
}

// -------------------------------------------------------------
// 6. Live Stopwatch / Session Timer
// -------------------------------------------------------------
let elapsedSeconds = 0;
let timerInterval = null;

function startLiveTimer(timerDisplayId) {
  const display = document.getElementById(timerDisplayId);
  if (!display) return;

  clearInterval(timerInterval);
  elapsedSeconds = 0;

  timerInterval = setInterval(() => {
    elapsedSeconds++;
    const mins = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
    const secs = String(elapsedSeconds % 60).padStart(2, "0");
    display.textContent = `${mins}:${secs}`;
  }, 1000);
}

// -------------------------------------------------------------
// 7. Clipboard Utilities
// -------------------------------------------------------------
function copyTextToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const origText = btnElement.innerHTML;
    btnElement.innerHTML = "✅ Copied!";
    setTimeout(() => {
      btnElement.innerHTML = origText;
    }, 2000);
  }).catch(() => {
    alert("Could not copy text to clipboard.");
  });
}
