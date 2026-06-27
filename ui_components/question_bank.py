import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def parse_question_bank(qb_text: str) -> list:
    """
    Parses canonical format from lemma_store._qb_to_markdown():

    ## TOPIC: Finite Automata
    ### Q1 | marks:5 | source:pyq | source_ref:PYQ-2023 | difficulty:medium
    QUESTION: What is a DFA?
    ANSWER: A DFA is a 5-tuple...
    KEYWORDS: dfa, automata
    ---

    Returns list of:
      { topic, questions: [{number, marks, source, difficulty, question, answer, keywords}] }
    """
    if not qb_text:
        return []

    # Strip code fences
    qb_text = re.sub(r"```[a-z]*\n?", "", qb_text).replace("```", "").strip()

    topics = []

    # Split on ## TOPIC: lines
    topic_blocks = re.split(r'\n##\s+TOPIC:\s*', qb_text)

    for block in topic_blocks:
        block = block.strip()
        if not block or block.startswith("# "):
            continue

        # First line is topic name
        lines = block.split("\n", 1)
        topic_name = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""

        if not topic_name:
            continue

        questions = _parse_questions_canonical(body)

        if questions:
            topics.append({
                "topic": topic_name,
                "questions": questions,
            })

    # Fallback: try old format if canonical parse yields nothing
    if not topics:
        topics = _parse_legacy_format(qb_text)

    return topics


def _parse_questions_canonical(body: str) -> list:
    """Parse ### Q1 | marks:5 | ... blocks."""
    questions = []

    # Split on ### Qn lines
    q_blocks = re.split(r'\n###\s+', body)

    for idx, block in enumerate(q_blocks):
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        header = lines[0]
        rest   = "\n".join(lines[1:])

        # Parse header: Q1 | marks:5 | source:pyq | source_ref:PYQ-2023 | difficulty:medium
        marks      = _extract_kv(header, "marks") or "—"
        source     = _extract_kv(header, "source") or "ai_generated"
        source_ref = _extract_kv(header, "source_ref") or ""
        difficulty = _extract_kv(header, "difficulty") or "medium"

        # Parse body fields
        question_text = _extract_field(rest, "QUESTION") or ""
        answer_text   = _extract_field(rest, "ANSWER")   or ""
        keywords      = _extract_field(rest, "KEYWORDS") or ""

        if not question_text:
            continue

        questions.append({
            "number":     str(idx + 1),
            "marks":      marks,
            "source":     _format_source(source, source_ref),
            "difficulty": difficulty,
            "question":   question_text.strip(),
            "answer":     _answer_to_points(answer_text),
            "keywords":   keywords.strip(),
        })

    return questions


def _extract_kv(header: str, key: str) -> str:
    """Extract key:value from pipe-separated header."""
    m = re.search(rf'\b{key}:([^|]+)', header, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_field(text: str, field: str) -> str:
    """Extract FIELD: value (single line)."""
    m = re.search(rf'^{field}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _format_source(source_type: str, source_ref: str) -> str:
    s = source_type.lower()
    if "pyq" in s:
        year = re.search(r'\d{4}', source_ref)
        return f"PYQ-{year.group()}" if year else "PYQ"
    elif "exercise" in s:
        return "Exercise"
    elif "assignment" in s:
        return "Assignment"
    else:
        return "AI-Generated"


def _answer_to_points(answer_text: str) -> list:
    """Convert answer string into list of bullet points."""
    if not answer_text:
        return []

    answer_text = answer_text.strip()

    # Numbered list
    if re.search(r'^\s*\d+\.\s+', answer_text, re.MULTILINE):
        items = re.split(r'\n\s*\d+\.\s+', '\n' + answer_text)
        return [re.sub(r'\*\*(.+?)\*\*', r'\1', i.strip()) for i in items if i.strip()]

    # Bullet list
    if re.search(r'^\s*[-*]\s+', answer_text, re.MULTILINE):
        return [
            re.sub(r'\*\*(.+?)\*\*', r'\1', re.sub(r'^[-*]\s*', '', line).strip())
            for line in answer_text.split('\n')
            if line.strip() and re.match(r'^\s*[-*]\s+', line)
        ]

    # Sentence split
    sentences = re.split(r'(?<=[.!?])\s+', answer_text)
    return [
        re.sub(r'\*\*(.+?)\*\*', r'\1', s.strip())
        for s in sentences if len(s.strip()) > 3
    ]


def _parse_legacy_format(text: str) -> list:
    """
    Fallback for old agent.py markdown format:
    ## Topic Name
    ### 📘 PYQ — 2023 — 2 Marks
    **Q:** ...
    **Answer:** ...
    """
    topics = []
    topic_blocks = re.split(r'\n##\s+(?!#)', text)

    for i, block in enumerate(topic_blocks):
        block = block.strip()
        if not block or '**Q' not in block:
            continue
        lines = block.split('\n', 1)
        topic_name = re.sub(r'[#*]', '', lines[0]).strip()
        body = lines[1] if len(lines) > 1 else ""
        if not topic_name:
            continue

        questions = []
        q_blocks = re.split(r'\n###\s+', body)
        for idx, qblock in enumerate(q_blocks):
            qblock = qblock.strip()
            if '**Q' not in qblock:
                continue
            first_line = qblock.split('\n', 1)[0]
            marks_m = re.search(r'(\d+)\s*Marks?', first_line, re.IGNORECASE)
            marks = marks_m.group(1) if marks_m else "—"
            year_m = re.search(r'(\d{4})', first_line)
            source = "AI-Generated"
            if "PYQ" in first_line.upper():
                source = f"PYQ-{year_m.group(1)}" if year_m else "PYQ"
            elif "EXERCISE" in first_line.upper():
                source = "Exercise"

            q_m = re.search(r'\*\*Q:?\*\*\s*(.*?)(?=\n\s*\*\*Answer|\Z)', qblock, re.DOTALL)
            a_m = re.search(r'\*\*Answer:?\*\*\s*(.*?)(?=\n\s*\*\*(?:Keywords|Source)|\Z)', qblock, re.DOTALL)
            kw_m = re.search(r'\*\*Keywords?:?\*\*\s*(.*?)(?=\n\s*\*\*Source|\Z)', qblock, re.DOTALL)

            q_text = re.sub(r'\s+', ' ', q_m.group(1).strip()) if q_m else ""
            a_text = a_m.group(1).strip() if a_m else ""
            kw     = kw_m.group(1).strip() if kw_m else ""

            if q_text:
                questions.append({
                    "number": str(idx),
                    "marks": marks,
                    "source": source,
                    "difficulty": "medium",
                    "question": q_text,
                    "answer": _answer_to_points(a_text),
                    "keywords": kw,
                })

        if questions:
            topics.append({"topic": topic_name, "questions": questions})

    return topics


# ─────────────────────────────────────────────────────────────
# BADGE / COLOR HELPERS
# ─────────────────────────────────────────────────────────────

def _marks_color(marks):
    try:
        m = int(marks)
        if m >= 10:
            return "#ef4444", "rgba(239,68,68,0.08)", "rgba(239,68,68,0.2)"
        elif m >= 5:
            return "#f59e0b", "rgba(245,158,11,0.08)", "rgba(245,158,11,0.2)"
        else:
            return "#3b82f6", "rgba(59,130,246,0.08)", "rgba(59,130,246,0.2)"
    except Exception:
        return "#888", "rgba(136,136,136,0.08)", "rgba(136,136,136,0.2)"


def _difficulty_badge(difficulty: str) -> str:
    d = difficulty.lower()
    if d == "hard":
        color, bg = "#ef4444", "rgba(239,68,68,0.1)"
        label = "HARD"
    elif d == "easy":
        color, bg = "#22c55e", "rgba(34,197,94,0.1)"
        label = "EASY"
    else:
        color, bg = "#f59e0b", "rgba(245,158,11,0.1)"
        label = "MEDIUM"
    return (
        f"<span style='background:{bg};color:{color};"
        f"border:1px solid {color}33;font-size:10px;"
        f"font-weight:600;padding:2px 7px;border-radius:4px;"
        f"font-family:Inter,sans-serif;'>{label}</span>"
    )


def _source_badge(source: str) -> str:
    s = source.upper()
    if "AI" in s or "GENERATED" in s:
        color, bg, label = "#8b5cf6", "rgba(139,92,246,0.12)", "AI"
    elif "EXERCISE" in s:
        color, bg, label = "#3b82f6", "rgba(59,130,246,0.12)", "EXERCISE"
    elif "ASSIGNMENT" in s:
        color, bg, label = "#06b6d4", "rgba(6,182,212,0.12)", "ASSIGNMENT"
    else:
        year_m = re.search(r'\d{4}', source)
        label  = f"PYQ {year_m.group()}" if year_m else "PYQ"
        color, bg = "#22c55e", "rgba(34,197,94,0.1)"
    return (
        f"<span style='background:{bg};color:{color};"
        f"border:1px solid {color}33;font-size:10px;"
        f"font-weight:600;padding:2px 7px;border-radius:4px;"
        f"font-family:Inter,sans-serif;'>{label}</span>"
    )


# ─────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────

def render_question_bank(data: dict):
    has_pyqs = data.get("has_pyqs", False)
    qb_text  = data.get("question_bank", "") or ""

    # Strip fences
    qb_text = re.sub(r"```[a-z]*\n?", "", qb_text).replace("```", "").strip()

    if not has_pyqs:
        st.markdown(
            "<div style='background:rgba(245,158,11,0.08);"
            "border:1px solid rgba(245,158,11,0.2);"
            "border-radius:8px;padding:10px 16px;margin-bottom:24px;'>"
            "<span style='color:#f59e0b;font-size:12px;font-weight:500;"
            "font-family:Inter,sans-serif;'>"
            "⚠ No PYQ files detected — questions generated from notes only."
            "</span></div>",
            unsafe_allow_html=True,
        )

    if not qb_text:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No question bank available.</div>",
            unsafe_allow_html=True,
        )
        return

    parsed_topics = parse_question_bank(qb_text)

    if not parsed_topics:
        st.warning("Could not parse questions. Showing raw output below.")
        with st.expander("Raw question bank"):
            st.text(qb_text[:5000])
        return

    # ── Topic selector ──
    topic_names = [t["topic"] for t in parsed_topics]
    total_q     = sum(len(t["questions"]) for t in parsed_topics)

    st.markdown(
        f"<p style='font-family:Inter,sans-serif;font-size:11px;"
        f"font-weight:600;letter-spacing:1.5px;text-transform:uppercase;"
        f"color:#888;margin:0 0 8px 0;'>{total_q} QUESTIONS ACROSS {len(topic_names)} TOPICS</p>",
        unsafe_allow_html=True,
    )

    selected_name = st.selectbox(
        label="topic_select",
        options=topic_names,
        label_visibility="collapsed",
    )

    selected = next(t for t in parsed_topics if t["topic"] == selected_name)

    st.markdown(
        f"<div style='border-bottom:1px solid #2a2a2a;padding-bottom:16px;"
        f"margin:20px 0 28px 0;'>"
        f"<h3 style='font-family:Inter,sans-serif;font-size:22px;"
        f"font-weight:700;color:#fff;margin:0 0 10px 0;'>{selected['topic']}</h3>"
        f"<span style='color:#555;font-family:JetBrains Mono,monospace;font-size:12px;'>"
        f"{len(selected['questions'])} questions</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Questions ──
    for i, q in enumerate(selected["questions"]):
        txt_color, bg, border = _marks_color(q["marks"])

        # Card header + question (answers NEVER shown in HTML — only via checkbox)
        st.markdown(
            f"<div style='border:1px solid #2a2a2a;border-radius:10px;"
            f"margin-bottom:4px;overflow:hidden;'>"
            f"<div style='background:#141414;padding:10px 18px;"
            f"border-bottom:1px solid #2a2a2a;display:flex;"
            f"align-items:center;gap:10px;flex-wrap:wrap;'>"
            f"<span style='font-family:JetBrains Mono,monospace;"
            f"font-size:11px;color:#555;'>Q{i+1}</span>"
            f"<span style='background:{bg};color:{txt_color};"
            f"border:1px solid {border};font-size:11px;font-weight:600;"
            f"padding:2px 8px;border-radius:4px;font-family:Inter,sans-serif;'>"
            f"{q['marks']} marks</span>"
            f"{_source_badge(q.get('source', ''))}"
            f"{_difficulty_badge(q.get('difficulty', 'medium'))}"
            f"</div>"
            f"<div style='padding:16px 18px;'>"
            f"<p style='font-family:Inter,sans-serif;font-size:15px;"
            f"font-weight:500;color:#e6e6e6;margin:0;line-height:1.6;'>"
            f"{q['question']}</p>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Answer toggle — key uses topic + index to avoid collisions
        safe_topic = re.sub(r'\W+', '_', selected_name)
        show = st.checkbox("Show answer", key=f"ans_{safe_topic}_{i}")

        if show:
            if q["answer"]:
                bullets = "".join(
                    f"<li style='margin-bottom:6px;line-height:1.7;'>{p}</li>"
                    for p in q["answer"]
                )
                kw_html = ""
                if q.get("keywords"):
                    kw_html = (
                        f"<p style='font-family:JetBrains Mono,monospace;"
                        f"font-size:10px;color:#888;margin:12px 0 0 0;'>"
                        f"keywords: {q['keywords']}</p>"
                    )
                st.markdown(
                    f"<div style='background:#0a140a;"
                    f"border-left:2px solid #22c55e;padding:14px 18px;"
                    f"margin-bottom:20px;border-radius:0 0 10px 10px;margin-top:-2px;'>"
                    f"<p style='font-family:JetBrains Mono,monospace;"
                    f"font-size:11px;color:#22c55e;letter-spacing:1px;"
                    f"margin:0 0 12px 0;'>// ANSWER</p>"
                    f"<ul style='font-family:Inter,sans-serif;color:#cccccc;"
                    f"font-size:14px;margin:0;padding-left:18px;"
                    f"line-height:1.9;'>{bullets}</ul>"
                    f"{kw_html}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='background:#0a140a;border-left:2px solid #444;"
                    "padding:14px 18px;margin-bottom:20px;"
                    "border-radius:0 0 10px 10px;margin-top:-2px;'>"
                    "<p style='font-family:JetBrains Mono,monospace;"
                    "font-size:11px;color:#555;margin:0;'>"
                    "// No answer data available</p></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)