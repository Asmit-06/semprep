"""
lemma_store.py
SEMPREP storage layer backed by Lemma tables.

Replaces JSON storage in datastore.py with structured Lemma table records.
All data lives in the cloud pod, visible in Lemma's web dashboard.

Usage:
    from lemma_store import save_subject_analysis, load_subject_analysis
    save_subject_analysis("DBMS", analysis_dict)
    data = load_subject_analysis("DBMS")
"""

import json
from datetime import datetime
from lemma_client import get_pod, _items


# ============================================================
# Internal Helpers
# ============================================================
def _pod():
    return get_pod()


def _to_json_safe(value):
    """Convert Python objects to JSON-storable strings for Lemma JSON columns."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    return str(value)

def _records(table: str, filter_dict: dict = None, limit: int = 500) -> list:
    """List records from a table, optionally filtered."""
    pod = _pod()
    kwargs = {"limit": limit}
    if filter_dict:
        kwargs["filter"] = [
            {"field": k, "op": "eq", "value": v} for k, v in filter_dict.items()
        ]
    res = pod.records.list(table, **kwargs)
    return _items(res)


def _delete_where(table: str, filter_dict: dict):
    """Delete all records matching the filter."""
    rows = _records(table, filter_dict)
    pod = _pod()
    for row in rows:
        rid = row.get("id") if isinstance(row, dict) else getattr(row, "id", None)
        if rid:
            pod.records.delete(table, rid)
    return len(rows)


def _row_to_dict(row):
    """Lemma records may come as dicts or objects. Normalize to dict."""
    if isinstance(row, dict):
        return row
    if hasattr(row, "to_dict"):
        return row.to_dict()
    return dict(row.__dict__) if hasattr(row, "__dict__") else {}


# ============================================================
# SUBJECTS
# ============================================================
def save_subject(name: str, zip_filename: str = "", code: str = "",
                 total_resources: int = 0, status: str = "ready"):
    """Upsert a subject row."""
    existing = _records("subjects", {"name": name})
    pod = _pod()
    data = {
        "name": name,
        "code": code,
        "zip_filename": zip_filename,
        "total_resources": total_resources,
        "status": status,
    }
    if existing:
        rid = _row_to_dict(existing[0]).get("id")
        pod.records.update("subjects", rid, data)
    else:
        pod.records.create("subjects", data)


def list_subjects() -> list:
    """Return list of subject names."""
    rows = _records("subjects")
    return [_row_to_dict(r).get("name") for r in rows if _row_to_dict(r).get("name")]


def get_subject(name: str) -> dict:
    rows = _records("subjects", {"name": name})
    return _row_to_dict(rows[0]) if rows else None


# ============================================================
# QUESTION BANK
# ============================================================
def save_question_bank_entries(subject: str, entries: list):
    if not entries:
        return 0
    _delete_where("question_bank", {"subject_name": subject})

    SOURCE_TYPE_MAP = {
        "pyq": "pyq", "PYQ": "pyq",
        "exercise": "exercise", "Exercise": "exercise",
        "assignment": "assignment", "Assignment": "assignment",
        "ai_generated": "ai_generated", "AI_Generated": "ai_generated",
        "ai-generated": "ai_generated", "AI-Generated": "ai_generated",
        "notes": "ai_generated", "Notes": "ai_generated",
    }
    DIFFICULTY_MAP = {
        "easy": "easy", "Easy": "easy",
        "medium": "medium", "Medium": "medium",
        "hard": "hard", "Hard": "hard",
    }

    rows = []
    for e in entries:
        src = e.get("source_type", "ai_generated")
        diff = e.get("difficulty", "medium")
        rows.append({
            "subject_name": subject,
            "question_text": e.get("question_text") or e.get("text") or "",
            "marks": int(e.get("marks") or 0),
            "topic": e.get("topic", ""),
            "source_type": SOURCE_TYPE_MAP.get(src, "ai_generated"),
            "source_reference": e.get("source_reference", ""),
            "answer": e.get("answer", ""),
            "keywords": _to_json_safe(e.get("keywords", [])),
            "difficulty": DIFFICULTY_MAP.get(diff, "medium"),
        })

    return _pod().records.bulk_create("question_bank", rows)

# ============================================================
# FLASHCARDS
# ============================================================
def save_flashcards(subject: str, cards: list):
    if not cards:
        return 0
    _delete_where("flashcards", {"subject_name": subject})
    rows = []
    for c in cards:
        rows.append({
            "subject_name": subject,
            "topic": c.get("topic", ""),
            "question": c.get("question") or c.get("front") or "",
            "answer": c.get("answer") or c.get("back") or "",
        })
    return _pod().records.bulk_create("flashcards", rows)


def load_flashcards(subject: str) -> list:
    rows = _records("flashcards", {"subject_name": subject})
    return [_row_to_dict(r) for r in rows]


# ============================================================
# CHEATSHEET
# ============================================================
def save_cheatsheet_entries(subject: str, entries: list):
    if not entries:
        return 0
    _delete_where("cheatsheet_entries", {"subject_name": subject})

    ENTRY_TYPE_MAP = {
        "concept": "concept", "Concept": "concept",
        "formula": "formula", "Formula": "formula",
        "definition": "definition", "Definition": "definition",
        "example": "example", "Example": "example",
        "fact": "concept", "Fact": "concept",
    }

    rows = []
    for e in entries:
        et = e.get("entry_type", "concept")
        rows.append({
            "subject_name": subject,
            "topic": e.get("topic", ""),
            "entry_type": ENTRY_TYPE_MAP.get(et, "concept"),
            "content": e.get("content", ""),
            "priority": int(e.get("priority") or 1),
        })
    return _pod().records.bulk_create("cheatsheet_entries", rows)


# ============================================================
# STUDY PLAN
# ============================================================
def save_study_plan(subject: str, days: list):
    """Each day: {day_number, topics, estimated_hours, date, status}"""
    if not days:
        return 0
    _delete_where("study_plan", {"subject_name": subject})

    STATUS_MAP = {
        "pending": "pending", "Pending": "pending",
        "in_progress": "in_progress", "In Progress": "in_progress",
        "completed": "completed", "Completed": "completed",
        "skipped": "skipped", "Skipped": "skipped",
    }

    rows = []
    for d in days:
        st = d.get("status", "pending")
        rows.append({
            "subject_name": subject,
            "day_number": int(d.get("day_number") or d.get("day") or 1),
            "date": d.get("date"),
            "topics": _to_json_safe(d.get("topics", [])),
            "estimated_hours": float(d.get("estimated_hours") or 2.0),
            "status": STATUS_MAP.get(st, "pending"),
        })
    return _pod().records.bulk_create("study_plan", rows)


# ============================================================
# TOPICS
# ============================================================
def save_topics(subject: str, topics: list):
    if not topics:
        return 0
    _delete_where("topics", {"subject_name": subject})
    rows = []
    for t in topics:
        rows.append({
            "subject_name": subject,
            "topic_name": t.get("topic_name") or t.get("name") or "",
            "weight": float(t.get("weight", 0.0)),
            "subtopics": _to_json_safe(t.get("subtopics", [])),
            "frequency": int(t.get("frequency", 0)),
        })
    return _pod().records.bulk_create("topics", rows)


def load_topics(subject: str) -> list:
    rows = _records("topics", {"subject_name": subject})
    return [_row_to_dict(r) for r in rows]


# ============================================================
# PYQS
# ============================================================
def save_pyqs(subject: str, pyqs: list):
    if not pyqs:
        return 0
    _delete_where("pyqs", {"subject_name": subject})
    rows = []
    for q in pyqs:
        rows.append({
            "subject_name": subject,
            "year": q.get("year", ""),
            "question_text": q.get("question_text") or q.get("text") or "",
            "marks": int(q.get("marks", 0)),
            "topic": q.get("topic", ""),
            "source_file": q.get("source_file", ""),
        })
    return _pod().records.bulk_create("pyqs", rows)


def load_pyqs(subject: str) -> list:
    rows = _records("pyqs", {"subject_name": subject})
    return [_row_to_dict(r) for r in rows]


# ============================================================
# FULL ANALYSIS — saves everything from agent.py output
# ============================================================
def save_full_analysis(subject: str, analysis: dict, zip_filename: str = ""):
    """
    Save a complete analysis result dict to Lemma tables.
    Handles BOTH:
      - Old format (markdown strings from agent.run_full_analysis)
      - New format (structured dicts from run_full_lemma_pipeline)
    """
    save_subject(
        name=subject,
        zip_filename=zip_filename,
        code=analysis.get("subject_code", ""),
        total_resources=analysis.get("file_count", 0),
        status="ready",
    )

    # ── TOPICS ─────────────────────────────────────────────────────────
    topics_input = analysis.get("topics") or _legacy_topics(analysis)
    if topics_input:
        normalized_topics = []
        for t in topics_input:
            if not isinstance(t, dict):
                continue
            normalized_topics.append({
                "topic_name": t.get("topic_name") or t.get("name") or "",
                "weight":     float(t.get("weight") or t.get("weightage") or 0),
                "subtopics":  t.get("subtopics", []),
                "frequency": _frequency_to_int(t),
            })
        if normalized_topics:
            save_topics(subject, normalized_topics)

    # ── QUESTION BANK ──────────────────────────────────────────────────
    qb = analysis.get("question_bank")
    if isinstance(qb, list) and qb:
        save_question_bank_entries(subject, [
            {
                "question_text":   q.get("question_text", ""),
                "marks":           int(q.get("marks") or 0),
                "topic":           q.get("topic", ""),
                "source_type":     q.get("source_type", "AI_Generated"),
                "source_reference": q.get("source_file", "") or q.get("source_reference", ""),
                "answer":          q.get("answer", ""),
                "keywords":        q.get("keywords", []),
                "difficulty":      q.get("difficulty", "Medium"),
            }
            for q in qb
        ])
        # Also save as markdown artifact for the existing UI that reads strings
        save_markdown_artifact(subject, "question_bank", _qb_to_markdown(qb))
    elif isinstance(qb, str) and qb:
        save_markdown_artifact(subject, "question_bank", qb)

    # ── FLASHCARDS ─────────────────────────────────────────────────────
    fc = analysis.get("flashcards")
    if isinstance(fc, list) and fc:
        save_flashcards(subject, [
            {
                "topic":    c.get("topic", ""),
                "question": c.get("front") or c.get("question") or "",
                "answer":   c.get("back") or c.get("answer") or "",
            }
            for c in fc
        ])
        save_markdown_artifact(subject, "flashcards", _flashcards_to_markdown(fc))
    elif isinstance(fc, str) and fc:
        save_markdown_artifact(subject, "flashcards", fc)

    # ── CHEATSHEET ─────────────────────────────────────────────────────
    cs = analysis.get("cheatsheet")
    if isinstance(cs, list) and cs:
        save_cheatsheet_entries(subject, [
            {
                "topic":      e.get("topic", ""),
                "content":    e.get("content", ""),
                "entry_type": e.get("entry_type", "concept"),
                "priority":   int(e.get("priority", 1)),
            }
            for e in cs
        ])
        save_markdown_artifact(subject, "cheatsheet", _cheatsheet_to_markdown(cs))
    elif isinstance(cs, str) and cs:
        save_markdown_artifact(subject, "cheatsheet", cs)

    # Also accept cheatsheet_text from new pipeline
    cs_text = analysis.get("cheatsheet_text")
    if cs_text and not isinstance(cs, list):
        save_markdown_artifact(subject, "cheatsheet", cs_text)

    # ── STUDY PLAN ─────────────────────────────────────────────────────
    sp = analysis.get("study_plan")
    if isinstance(sp, list) and sp:
        save_study_plan(subject, [
            {
                "day_number":      int(d.get("day") or d.get("day_number") or i + 1),
                "topics":          d.get("topics", []),
                "estimated_hours": float(d.get("estimated_hours", 2.0)),
                "status":          d.get("status", "pending"),
                "date":            d.get("date"),
            }
            for i, d in enumerate(sp)
        ])
        save_markdown_artifact(subject, "study_plan", _study_plan_to_markdown(sp))
    elif isinstance(sp, str) and sp:
        save_markdown_artifact(subject, "study_plan", sp)

    # ── PYQS ───────────────────────────────────────────────────────────
    pyqs = analysis.get("pyqs")
    if isinstance(pyqs, list) and pyqs:
        save_pyqs(subject, [
            {
                "year":          str(q.get("year", "")),
                "question_text": q.get("question_text", ""),
                "marks":         int(q.get("marks") or 0),
                "topic":         q.get("topic", ""),
                "source_file":   q.get("source_file", ""),
            }
            for q in pyqs
        ])

    # ── PRIORITY LIST (markdown) ──────────────────────────────────────
    pl = analysis.get("priority_list")
    if pl:
        if isinstance(pl, str):
            save_markdown_artifact(subject, "priority_list", pl)
        elif isinstance(pl, list):
            save_markdown_artifact(subject, "priority_list", _priority_to_markdown(pl))


# ============================================================
# Format converters — UPDATED: machine-parseable canonical format
# ============================================================

def _legacy_topics(analysis: dict) -> list:
    """Extract topics list from the OLD weighted_topics format."""
    wt = analysis.get("weighted_topics", {})
    if isinstance(wt, dict):
        return wt.get("weighted_topics") or wt.get("topics") or []
    if isinstance(wt, list):
        return wt
    return []


def _frequency_to_int(t: dict) -> int:
    """Convert frequency (string 'high'/'medium'/'low' or int) to int."""
    f = t.get("frequency")
    if isinstance(f, int):
        return f
    if isinstance(f, str):
        return {"high": 3, "medium": 2, "low": 1}.get(f.lower(), 0)
    if "years_appeared" in t and isinstance(t["years_appeared"], list):
        return len(t["years_appeared"])
    return 0


def _qb_to_markdown(qb: list) -> str:
    """
    Canonical format read by ui_components/question_bank.py

    ## TOPIC: Finite Automata
    ### Q1 | marks:5 | source:pyq | source_ref:PYQ-2023 | difficulty:medium
    QUESTION: What is a DFA?
    ANSWER: A DFA is a 5-tuple...
    KEYWORDS: dfa, automata, states
    ---
    """
    lines = ["# Question Bank\n"]

    # Group by topic
    by_topic = {}
    for q in qb:
        t = q.get("topic") or "General"
        by_topic.setdefault(t, []).append(q)

    for topic, questions in by_topic.items():
        lines.append(f"## TOPIC: {topic}")
        for i, q in enumerate(questions, 1):
            src_type = q.get("source_type", "ai_generated")
            src_ref  = q.get("source_reference", "") or q.get("source_file", "")
            marks    = q.get("marks", 0)
            diff     = q.get("difficulty", "medium")
            lines.append(
                f"### Q{i} | marks:{marks} | source:{src_type}"
                f" | source_ref:{src_ref} | difficulty:{diff}"
            )
            lines.append(f"QUESTION: {q.get('question_text', '').strip()}")
            ans = q.get("answer", "")
            if ans:
                lines.append(f"ANSWER: {str(ans).strip()}")
            kw = q.get("keywords", [])
            if kw:
                if isinstance(kw, list):
                    kw = ", ".join(str(k) for k in kw)
                lines.append(f"KEYWORDS: {kw}")
            lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _flashcards_to_markdown(fc: list) -> str:
    """
    Canonical format read by ui_components/flashcards.py

    ## TOPIC: OSI Model
    FRONT: What is layer 2?
    BACK: Data Link Layer
    ---
    """
    lines = ["# Flashcards\n"]

    by_topic = {}
    for c in fc:
        t = c.get("topic") or "General"
        by_topic.setdefault(t, []).append(c)

    for topic, cards in by_topic.items():
        lines.append(f"## TOPIC: {topic}")
        for c in cards:
            front = c.get("front") or c.get("question", "")
            back  = c.get("back")  or c.get("answer",   "")
            lines.append(f"FRONT: {front.strip()}")
            lines.append(f"BACK: {back.strip()}")
            lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _cheatsheet_to_markdown(cs: list) -> str:
    """
    Canonical format read by ui_components/cheatsheet.py

    ## TOPIC: OSI Model
    TYPE: concept
    PRIORITY: 3
    CONTENT: The OSI model has 7 layers...
    ---
    """
    lines = ["# Cheatsheet\n"]

    by_topic = {}
    for e in cs:
        t = e.get("topic") or "General"
        by_topic.setdefault(t, []).append(e)

    for topic, entries in by_topic.items():
        lines.append(f"## TOPIC: {topic}")
        for e in entries:
            lines.append(f"TYPE: {e.get('entry_type', 'concept')}")
            lines.append(f"PRIORITY: {e.get('priority', 1)}")
            lines.append(f"CONTENT: {e.get('content', '').strip()}")
            lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _study_plan_to_markdown(sp: list) -> str:
    """
    Canonical format read by ui_components/study_plan.py

    ## DAY: 1
    TOPICS: Finite Automata||Regular Expressions
    HOURS: 2.0
    STATUS: pending
    FOCUS: Master DFA construction
    ---
    """
    lines = ["# Study Plan\n"]

    for i, d in enumerate(sp):
        day    = d.get("day") or d.get("day_number") or (i + 1)
        topics = d.get("topics", [])
        if isinstance(topics, list):
            topics_str = "||".join(str(t).strip() for t in topics)
        else:
            topics_str = str(topics).strip()
        hours  = d.get("estimated_hours", 2.0)
        status = d.get("status", "pending")
        focus  = d.get("focus", "")

        lines.append(f"## DAY: {day}")
        lines.append(f"TOPICS: {topics_str}")
        lines.append(f"HOURS: {hours}")
        lines.append(f"STATUS: {status}")
        if focus:
            lines.append(f"FOCUS: {focus}")
        if d.get("questions_to_practice"):
            lines.append(f"QUESTIONS: {d.get('questions_to_practice')}")
        if d.get("flashcards_to_review"):
            lines.append(f"FLASHCARDS: {d.get('flashcards_to_review')}")
        lines.append("---")

    return "\n".join(lines)


def _priority_to_markdown(pl: list) -> str:
    """
    Canonical format read by ui_components/priority_list.py

    ## ITEM: 1
    TOPIC: Finite Automata
    WEIGHT: 0.85
    BAND: HIGH
    SUBTOPICS: DFA, NFA, epsilon-closure
    ---
    """
    lines = ["# Priority List\n"]

    for i, item in enumerate(pl, 1):
        if isinstance(item, dict):
            topic     = item.get("topic") or item.get("topic_name", "")
            weight    = item.get("weight") or item.get("weightage", 0)
            band      = item.get("band") or item.get("priority", "MEDIUM")
            subtopics = item.get("subtopics", [])
            if isinstance(subtopics, list):
                subtopics = ", ".join(str(s) for s in subtopics)
            lines.append(f"## ITEM: {i}")
            lines.append(f"TOPIC: {topic}")
            lines.append(f"WEIGHT: {weight}")
            lines.append(f"BAND: {band}")
            if subtopics:
                lines.append(f"SUBTOPICS: {subtopics}")
            lines.append("---")
        else:
            lines.append(f"## ITEM: {i}")
            lines.append(f"TOPIC: {str(item)}")
            lines.append(f"WEIGHT: 0")
            lines.append(f"BAND: MEDIUM")
            lines.append("---")

    return "\n".join(lines)


def load_full_analysis(subject: str) -> dict:
    """
    Reconstruct an analysis dict from Lemma tables in the shape your UI expects.
    """
    if not get_subject(subject):
        return None

    topics = load_topics(subject)
    weighted_topics = {
        "weighted_topics": [
            {
                "topic_name": t.get("topic_name"),
                "weight": t.get("weight"),
                "subtopics": _json_or_list(t.get("subtopics")),
            }
            for t in topics
        ]
    }

    return {
        "subject": subject,
        "weighted_topics": weighted_topics,
        "topic_map": {},  # legacy, not used by UI
        "priority_list": load_markdown_artifact(subject, "priority_list"),
        "question_bank": load_markdown_artifact(subject, "question_bank"),
        "flashcards": load_markdown_artifact(subject, "flashcards"),
        "study_plan": load_markdown_artifact(subject, "study_plan"),
        "cheatsheet": load_markdown_artifact(subject, "cheatsheet"),
        "has_pyqs": len(load_pyqs(subject)) > 0,
        "last_updated": datetime.now().isoformat(),
    }


def _json_or_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return []
    return []


# ============================================================
# MARKDOWN ARTIFACTS (transitional — for existing string outputs)
# Stored in cheatsheet_entries as a single entry of entry_type=concept
# with topic="__artifact__" and content=markdown text
# ============================================================
ARTIFACT_TOPIC_PREFIX = "__artifact__"


def save_markdown_artifact(subject: str, kind: str, markdown: str):
    """Store a markdown blob like question_bank or cheatsheet text."""
    if not markdown:
        return
    artifact_topic = f"{ARTIFACT_TOPIC_PREFIX}::{kind}"

    # Delete previous artifact of this kind
    rows = _records("cheatsheet_entries", {"subject_name": subject, "topic": artifact_topic})
    pod = _pod()
    for r in rows:
        rid = _row_to_dict(r).get("id")
        if rid:
            pod.records.delete("cheatsheet_entries", rid)

    pod.records.create("cheatsheet_entries", {
        "subject_name": subject,
        "topic": artifact_topic,
        "entry_type": "concept",
        "content": markdown,
        "priority": 0,
    })


def load_markdown_artifact(subject: str, kind: str) -> str:
    artifact_topic = f"{ARTIFACT_TOPIC_PREFIX}::{kind}"
    rows = _records("cheatsheet_entries", {"subject_name": subject, "topic": artifact_topic})
    if rows:
        return _row_to_dict(rows[0]).get("content", "")
    return ""


# ============================================================
# Standalone Test
# ============================================================
if __name__ == "__main__":
    print("Testing Lemma store...\n")

    print("Creating test subject 'TEST_SUBJECT'...")
    save_subject(name="TEST_SUBJECT", zip_filename="test.zip", total_resources=3)

    print("Subjects in pod:")
    for s in list_subjects():
        print(f"  - {s}")

    print("\nSaving 2 flashcards...")
    save_flashcards("TEST_SUBJECT", [
        {"topic": "OSI", "question": "What is layer 2?", "answer": "Data Link"},
        {"topic": "OSI", "question": "What is layer 3?", "answer": "Network"},
    ])

    print("Loading flashcards back:")
    for c in load_flashcards("TEST_SUBJECT"):
        print(f"  Q: {c.get('question')}  A: {c.get('answer')}")

    print("\nSaving markdown artifact (question_bank)...")
    save_markdown_artifact("TEST_SUBJECT", "question_bank",
                           "# Question Bank\n\n1. Q1?\n2. Q2?")

    print("Loading back:")
    print(load_markdown_artifact("TEST_SUBJECT", "question_bank"))

    print("\nDone. Check Lemma UI: https://lemma.work/")