<div align="center">

<img width="1428" height="317" alt="Screenshot 2026-06-26 222544" src="https://github.com/user-attachments/assets/eed8c1dd-15f2-4516-948d-df6816e74ebe" />



<br/>

# S E M P R E P

### 🎓 Last-Minute Saviour for Semester Examinations

*Transform scattered PDFs, PYQs, assignments, and handwritten notes into a complete exam preparation strategy — in minutes.*

<br/>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Lemma SDK](https://img.shields.io/badge/Lemma_SDK-Powered-6C63FF?style=for-the-badge)
![Minimax](https://img.shields.io/badge/Runtime-Minimax_M3-FFD700?style=for-the-badge)
![Hackathon](https://img.shields.io/badge/Gappy_AI_National_Hackathon-2026-FF6B35?style=for-the-badge)

<br/>



</div>

---

## 🎬 Demo




https://github.com/user-attachments/assets/7f66a236-90cb-4052-aa5d-21710e25ff30


---



🏢 **Lemma Pod (for judges):** Access granted to `ayush@gappy.ai`

---

## 🚨 The Problem

Every semester, Indian engineering students receive study materials from multiple sources — and before exams, valuable time is spent **organising files instead of studying**.

<br/>

| Source | Problem |
|--------|---------|
| 📄 Previous Year Questions | Scattered across multiple PDFs |
| 📝 Lecture Notes | No indication of what's important |
| 📋 Assignments | Mixed with unrelated material |
| ✏️ Handwritten Notes | Poor OCR, hard to search |
| 📚 Reference PDFs | Hundreds of pages, no prioritisation |

<br/>

> **Students struggle to answer:**
> *"Which topics are most important? What questions are likely to appear? How should I plan my remaining days?"*

---

## 💡 The Solution

SEMPREP converts a **single ZIP file** of study material into a complete AI-powered exam preparation system.

```
Upload ZIP  ─▶  Detect Subjects  ─▶  Analyse Topics  ─▶  Generate Questions  ─▶  Build Flashcards  ─▶  Study Plan
```

<br/>

| | What SEMPREP Does Automatically |
|--|-------------------------------|
| ✅ | Detects subjects from filenames and content |
| ✅ | Extracts important topics and concepts |
| ✅ | Identifies high-weight exam concepts |
| ✅ | Generates **25–30 practice questions** per subject |
| ✅ | Creates model answers with keywords |
| ✅ | Builds **30+ revision flashcards** |
| ✅ | Produces topic-grouped cheat sheets |
| ✅ | Creates a personalised **day-by-day study plan** |
| ✅ | Adapts to your deadline — `5 days → Fast Mode` · `2 days → Crisis Mode` |

---

## ✨ Features

<details>
<summary><b>📚 Smart Subject Detection</b></summary>
<br/>

Automatically identifies subjects using a **two-layer system**:

- **Layer 1 —** Fast keyword matching on filenames for obvious cases
- **Layer 2 —** Agent-based content analysis for ambiguous files

Supports **multiple subjects in a single ZIP** — each gets its own full pipeline run.

<br/>
</details>

<details>
<summary><b>🎯 Topic Priority Ranking</b></summary>
<br/>

Ranks topics based on frequency of appearance in PYQs, importance, and exam relevance.

| Priority | Threshold | Meaning |
|----------|-----------|---------|
| 🔴 **Critical** | 75%+ of past papers | Study this first — always comes up |
| 🟠 **High Priority** | 50–75% of past papers | Very likely to appear |
| 🟢 **Medium Priority** | Appears occasionally | Cover if time allows |

<br/>
</details>

<details>
<summary><b>❓ AI Question Bank</b></summary>
<br/>

Generates expected exam questions with full metadata:

- **Topic-wise classification** — know what chapter each question belongs to
- **Marks weighting** — 2 / 5 / 10 mark questions generated separately
- **Source tagging** — PYQ year / AI Generated / Exercise
- **Model answers** — hidden by default, revealed on demand for self-testing
- **Important keywords** — per answer for rapid revision

<br/>
</details>

<details>
<summary><b>🧠 Flashcards</b></summary>
<br/>

Creates quick-revision cards covering:
- Definitions and formulas
- Key concepts and theorems
- Frequently asked short-answer topics

Features **front-only display** with a Flip button, a **topic filter** for targeted revision, and a **card navigator with a progress bar**.

<br/>
</details>

<details>
<summary><b>📄 Cheat Sheets</b></summary>
<br/>

Condensed quick-reference material grouped by topic. **High-priority topics auto-expanded.** Weak topics highlighted based on your progress tracker data.

<br/>
</details>

<details>
<summary><b>📅 Study Planner</b></summary>
<br/>

Generates a personalised day-by-day roadmap based on:
- Days remaining until your exam
- Topic priority weights from the analyser
- Question bank size and flashcard count

Each day shows **estimated hours**, **topics to cover**, and **practice targets**.

<br/>
</details>

<details>
<summary><b>📈 Progress Tracking</b></summary>
<br/>

Track your preparation status per topic in real time:

| Status | Meaning |
|--------|---------|
| ✅ Mastered | Confident — move on |
| ⚠ Weak | Needs more revision |
| — Skipped | Deliberately left out |
| 🕐 Pending | Not yet reviewed |

Overall mastery percentage updates live as you mark topics.

<br/>
</details>

---

## 🤖 Agent Pipeline

SEMPREP uses a **9-Agent Architecture** built entirely with Lemma SDK.
Each agent is **stateless** — pure text in, structured JSON out. One job per agent.

<br/>

| Agent | Phase | Execution | Responsibility |
|-------|-------|-----------|----------------|
| `subject_detector` | 1 | Sequential | Detects actual subject from content, not just filename |
| `resource_classifier` | 1 | Sequential | Categorises files — PYQ, Notes, Reference, Assignment |
| `extractor` | 1 | Sequential | Pulls raw questions, topics, and key concepts |
| `topic_analyzer` | 1 | Sequential | Calculates topic importance and weights by exam frequency |
| `question_bank_coach` | 2 | **Parallel** | Generates 25–30 expected exam questions |
| `answer_writer` | 2 | Parallel (chained) | Creates model answers with keywords and difficulty tags |
| `flashcard_maker` | 2 | **Parallel** | Generates 30+ front/back revision cards |
| `cheatsheet_writer` | 2 | **Parallel** | Builds quick-reference notes grouped by topic |
| `planner` | 2 | **Parallel** | Generates a day-by-day schedule based on deadline |

---

## 🏗️ Architecture

```
ZIP Upload
      │
      ▼
file_processor.py          [Pure Python — no LLM]
      │  Extracts text, runs OCR (PyMuPDF + Tesseract), buckets by subject
      ▼
workflows.py               [Orchestration layer]
      │  One pipeline per subject · Retry on timeout
      ▼
lemma_pipeline.py          [9 Lemma Agents]
      │
      ├── Layer 1 · Understanding
      │     subject_detector → resource_classifier
      │     → extractor → topic_analyzer
      │
      ├── Layer 2 · Generation  [ThreadPoolExecutor — runs concurrently]
      │     question_bank_coach → answer_writer
      │     → flashcard_maker → cheatsheet_writer
      │
      └── Layer 3 · Planning
            planner
      │
      ▼
lemma_store.py             [Storage — 10 Lemma Tables · 5 Markdown Artifacts]
      │
      ▼
datastore.py               [Cache Layer · ttl=300]
      │  Pre-warms on startup · Subject switching is instant after first load
      ▼
Streamlit Dashboard        [6-Tab Interface]
      Priority → Questions → Flashcards → Study Plan → Cheatsheet → Progress
```

### Pipeline Flow

<div align="center">
<img width="766" height="369" alt="WhatsApp Image 2026-06-27 at 6 53 52 PM" src="https://github.com/user-attachments/assets/e4a7fee9-d283-4a73-9d5c-cd46d3ea4dd9" />

</div>

The uploaded ZIP is processed and routed through the complete SEMPREP pipeline:


### Agent Details

<div align="center">
<img width="1423" height="1062" alt="WhatsApp Image 2026-06-27 at 6 51 07 PM" src="https://github.com/user-attachments/assets/cfc8043c-ecb8-42f4-b936-15985aa7d897" />


</div>

#### Phase 1 — Understanding Layer

1. `subject_detector`
2. `resource_classifier`
3. `extractor`
4. `topic_analyzer`

This phase identifies subjects, classifies resources, extracts information, and ranks topics based on exam relevance.

#### Phase 2 — Generation Layer  *(runs concurrently via ThreadPoolExecutor)*

- `question_bank_coach` → `answer_writer`
- `flashcard_maker`
- `cheatsheet_writer`
- `planner`

This phase generates revision material, practice questions, model answers, flashcards, cheat sheets, and personalized study plans.


---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + custom CSS |
| Backend | Python 3.13 |
| AI Agents | Lemma SDK |
| Data Storage | Lemma Datastores (10 typed tables) |
| OCR Engine | PyMuPDF + Tesseract |
| LLM Runtime | Minimax M3 via Lemma billing |

---

## 📊 Lemma SDK Usage

| Component | How Used |
|-----------|---------|
| **Agents** | 9 purpose-built agents, pure text-in JSON-out, no tools |
| **Datastores** | 10 structured tables with typed columns and enum validation |
| **Records API** | `bulk_create`, `list` with filters, `update`, `delete` |
| **Conversations API** | `create_for_agent`, `send_stream`, poll loop, message read |
| **Runtime** | Minimax M3 via Lemma's native billing |


### Advanced SDK Utilisation

Unlike the common workflow of attaching an external OpenAI or Anthropic API key to a hosted pod, SEMPREP runs entirely on Lemma's native infrastructure.

- 9 Lemma Agents
- 10 Typed Lemma Datastores
- Lemma Conversations API
- Lemma Records API
- Minimax M3 Runtime via Lemma Billing

Storage, inference, agent orchestration, and billing are all handled through Lemma, demonstrating end-to-end SDK adoption without reliance on external AI providers.

<br/>

## 🌐 Deployment Architecture

| Component | Where It Runs |
|-----------|--------------|
| Lemma Pod | Hosted on lemma.work |
| Agent Runtime | Minimax M3 via Lemma billing |
| Storage | 10 Lemma Datastores |
| Agent Orchestration | Lemma Conversations API |
| Streamlit UI | Streamlit Community Cloud |
| Authentication | Lemma CLI token (`~/.lemma/config.json`) |

### Why This Matters

SEMPREP runs entirely on Lemma's hosted infrastructure.

- No Docker deployment required
- No local Lemma installation required
- No external OpenAI or Anthropic API keys required
- No self-hosted database required

Judges can evaluate the project directly through the live Streamlit application and the shared Lemma pod.

<br/>

### Lemma Tables (10 tables)

| Table | What It Stores |
|-------|---------------|
| `subjects` | name, code, zip_filename, status |
| `topics` | topic_name, weight, subtopics, frequency |
| `question_bank` | question_text, marks, topic, source_type, answer, keywords, difficulty |
| `flashcards` | topic, front, back |
| `cheatsheet_entries` | topic, content, entry_type, priority |
| `study_plan` | day_number, topics, estimated_hours, status |
| `pyqs` | year, question_text, marks, topic, source_file |
| `progress` | weak_topics, mastered_topics, skipped_topics |
| `resources` | filename, file_type, subject |
| `sessions` | session metadata |

---

## ⚡ Performance Optimizations

| Metric | Before | After |
|--------|--------|-------|
| Pipeline runtime | ~15 min | ~5 min (parallel execution) |
| Subject switching | 8+ sec | <1 sec (cache pre-warming) |
| Tab switching | Lag | Instant |
| Network timeout recovery | Manual restart | Auto-retry (3 attempts) |

### How
- **Phase 2 agents** (`question_bank_coach + answer_writer`, `flashcard_maker`, `cheatsheet_writer`, `planner`) run concurrently via `ThreadPoolExecutor` after Phase 1 completes
- **Cache pre-warming** on app startup loads all subjects into `st.cache_data` (ttl=300)
- **Retry logic** on `create_for_agent` and pipeline calls handles ConnectTimeout, LemmaTimeout, and 503 errors gracefully

---

## 📸 Screenshots

<div align="center">

### Dashboard — Progress Tracker
<img width="1846" height="807" alt="Screenshot 2026-06-26 225449" src="https://github.com/user-attachments/assets/5dd2ba57-3619-460f-a928-04fcd6afa83f" />


<br/>

### Lemma Agents Panel
<img width="1895" height="883" alt="Screenshot 2026-06-26 225639" src="https://github.com/user-attachments/assets/6db8d90a-d373-4363-8003-d693eeb400ed" />


<br/>

### PYQs Data Table (112 records)
<img width="1896" height="805" alt="Screenshot 2026-06-26 225729" src="https://github.com/user-attachments/assets/f954e04d-a6fa-4f86-9e3f-920d4bfa3ce0" />



<br/>

### Question Bank (293 records)
<img width="1901" height="858" alt="Screenshot 2026-06-26 225756" src="https://github.com/user-attachments/assets/a62945d5-9595-4054-a1f0-0b549cc35ed8" />


</div>

## ⚡ Quick Start for Judges (No Local Setup Required)

SEMPREP uses a hosted Lemma pod and Lemma's built-in Minimax M3 runtime.

### Evaluate the Project

#### Option 1 — Use the Live Application

1. Open the Streamlit application: **https://semprep-oursemprep.streamlit.app**
2. Upload a ZIP containing notes, PYQs, assignments, or PDFs
3. Review generated outputs

#### Option 2 — Inspect the Lemma Backend

Pod access has been granted to:

`ayush@gappy.ai`

Judges can:

- Browse all 10 Lemma Tables
- Inspect all 9 deployed Agents
- Review agent conversations
- Verify generated records
- Inspect stored artifacts and outputs

### What to Verify

- Subject detection
- Resource classification
- Topic prioritization
- Question bank generation
- Model answer generation
- Flashcard creation
- Cheat sheet generation
- Study plan creation
- Data persistence inside Lemma tables

### Requirements

✅ No Docker

✅ No WSL

✅ No Local Lemma Installation

✅ No External API Keys

✅ Fully Hosted Evaluation

---

## 🚀 Installation

### Prerequisites

- Python 3.13+
- Tesseract OCR installed and in PATH
- A Lemma account with a configured pod

### System Dependencies

For Streamlit Cloud / Linux deployment, create `packages.txt` in the project root:

```
tesseract-ocr
tesseract-ocr-eng
poppler-utils
```

For Windows local, install Tesseract from [UB Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki).

### Clone & Set Up

```bash
git clone https://github.com/YOUR_USERNAME/semprep.git
cd semprep
python -m venv venv
```

**Activate the environment:**

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

```bash
# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

#### For Local Development

Create a `.env` file in the project root:

```env
LEMMA_API_URL=https://api.lemma.work
LEMMA_POD_ID=your_pod_id
LEMMA_ORG_ID=your_org_id
LEMMA_CONFIG_PATH=C:\Users\YourName\.lemma\config.json
LEMMA_TIMEOUT=600
```

### First-Time Agent Setup

```bash
# Create all tables (run once only)
python create_tables.py
```

```bash
# Create all 9 Lemma Agents (run once only)
python create_agents.py
```

### Run

```bash
streamlit run main.py
```

---

## 📁 Project Structure

```
semprep/
├── main.py                   # Streamlit app — UI entry point
├── workflows.py              # Pipeline orchestration + retry logic
├── lemma_pipeline.py         # 9 Lemma agents end-to-end
├── lemma_store.py            # Lemma tables read/write layer
├── lemma_client.py           # Lemma SDK connection + pod init
├── datastore.py              # Cache layer (ttl=300 · pre-warms on startup)
├── file_processor.py         # ZIP extraction + OCR + subject bucketing
├── create_agents.py          # One-time agent creation script
├── clear_subjects.py         # Wipe Lemma tables for a clean test run
├── packages.txt              # System dependencies for Streamlit Cloud
├── ui_components/
│   ├── __init__.py
│   ├── question_bank.py      # Q&A with hidden answers
│   ├── flashcards.py         # Flip card navigator
│   ├── cheatsheet.py         # Topic-grouped reference
│   ├── study_plan.py         # Day-by-day planner
│   ├── priority_list.py      # Weighted topic ranking
│   └── progress.py           # Mastered / Weak / Skipped tracker
├── screenshots/              # Dashboard preview images
├── .env                      # Not committed — configure manually
├── .gitignore
└── requirements.txt
```

---

## ⚠️ Design Decisions & Known Constraints

| Constraint | How It Is Handled |
|------------|------------------|
| Handwritten notes with poor OCR | Detected and flagged — user guided to re-scan or provide as `.txt` |
| 15–20 min first-run processing time | Results cached in Lemma tables — all tabs load instantly on return visits |
| Subject misclassification | Two-layer detection: keyword matching + agent content analysis. Manual rename available from dashboard |
| Binary / unreadable files | Automatically skipped with a terminal notification |
| Streamlit Cloud token expiry | App reads full Lemma config JSON from secrets; SDK auto-refreshes access tokens using `refresh_token` (lasts weeks) |

---

## 🔮 Future Scope

| Feature | Description |
|---------|-------------|
| 🔄 Idempotent Resume | Skip already-completed agents on partial pipeline failure |
| 📱 Mobile App | iOS and Android client |
| 🎙️ Voice Assistant | Voice-based study companion |
| 🔁 Adaptive Quizzing | Spaced repetition based on weak topics |
| 🌐 Multi-Language | Regional language support |
| 📊 Semester Analytics | Performance tracking across multiple exams |
| 👥 Study Groups | Collaborative preparation rooms |
| 🏫 LMS Integration | Direct sync with college portals |

---

## 🏆 Hackathon Submission

> **Event:** Gappy AI National Hackathon 2026
> **Theme:** AI Learning Companion
> **Project:** SEMPREP

**Problem solved:**
Indian engineering students receive study material scattered across PDFs, PYQs, and handwritten notes with no structured way to prioritise what to study. The night before exams, students sort files instead of studying. SEMPREP takes one ZIP file and produces a ranked priority list, question bank with model answers, flashcards, cheatsheet, and a day-by-day study plan — fully automated using 9 Lemma agents.

**Solution approach:**
SEMPREP runs a 9-agent pipeline on Lemma SDK. Each agent has one job: subject detection, resource classification, text extraction, topic weighting, question generation, answer writing, flashcard creation, cheatsheet writing, and study planning. Results are stored in 10 structured Lemma tables and rendered in a 6-tab Streamlit dashboard. The pipeline adapts to days remaining — 5 days triggers Fast Mode, 2 days triggers Crisis Mode. Phase 2 agents run concurrently via `ThreadPoolExecutor`, cutting total runtime from ~15 minutes to ~5 minutes.

**SDK utilisation:**
Used Lemma agents (9 agents), Lemma datastores (10 typed tables), Records API (`bulk_create`, `filter`, `update`, `delete`), Conversations API (`create_for_agent`, `send_stream`, poll loop), and Minimax M3 runtime via Lemma's own billing. Storage, inference, and agent orchestration all run through Lemma.

---

## 👨‍💻 Author

**Swapnajit Mohapatra**
<br/>
**Asmit Chhotaray**


[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/swapnajit-mohapatra-b2743331b/) - Swapnajit Mohapatra

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/asmit-chhotaray-375003373/) - Asmit Chhotaray

---

<div align="center">

### ⭐ If this helped you, give it a star!

*Built with [Lemma SDK](https://lemma.work) — open-source infrastructure for AI-native software.*

`Python 3.13` · `Streamlit` · `Minimax M3` · `PyMuPDF + Tesseract` · `Lemma Datastores`

</div>
