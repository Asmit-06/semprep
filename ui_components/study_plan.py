import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def parse_study_plan(sp_text: str) -> list:
    """
    Canonical format:
        ## DAY: 1
        TOPICS: Finite Automata||Regular Expressions
        HOURS: 2.0
        STATUS: pending
        FOCUS: Master DFA construction
        ---

    Returns list of {day, topics, hours, status, focus}
    """
    if not sp_text:
        return []

    sp_text = re.sub(r"```[a-z]*\n?", "", sp_text).replace("```", "").strip()

    days = []

    day_blocks = re.split(r'\n##\s+DAY:\s*', sp_text)

    for block in day_blocks:
        block = block.strip()
        if not block or block.startswith("# "):
            continue

        lines = block.split("\n", 1)
        try:
            day_num = int(lines[0].strip())
        except ValueError:
            day_num = len(days) + 1

        body = lines[1] if len(lines) > 1 else ""

        # Topics: split by || (canonical) or comma (legacy)
        topics_raw = _field(body, "TOPICS") or ""
        if "||" in topics_raw:
            topics = [t.strip() for t in topics_raw.split("||") if t.strip()]
        else:
            topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

        hours_raw = _field(body, "HOURS") or "2.0"
        try:
            hours = float(hours_raw)
        except Exception:
            hours = 2.0

        status = _field(body, "STATUS") or "pending"
        focus  = _field(body, "FOCUS")  or ""
        questions = _field(body, "QUESTIONS") or ""
        flashcards_review = _field(body, "FLASHCARDS") or ""

        days.append({
            "day":       day_num,
            "topics":    topics,
            "hours":     hours,
            "status":    status,
            "focus":     focus,
            "questions": questions,
            "flashcards": flashcards_review,
        })

    # Fallback
    if not days:
        days = _parse_legacy_study_plan(sp_text)

    return sorted(days, key=lambda d: d["day"])


def _field(text: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _parse_legacy_study_plan(text: str) -> list:
    """Fallback: ## Day N / **Topics:** format."""
    days = []
    blocks = re.split(r'\n##\s+Day\s+', text, flags=re.IGNORECASE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 1)
        try:
            day_num = int(lines[0].strip())
        except Exception:
            continue
        body = lines[1] if len(lines) > 1 else ""

        topics_m = re.search(r'\*\*Topics?:?\*\*\s*(.+)', body)
        hours_m  = re.search(r'\*\*Estimated hours?:?\*\*\s*([\d.]+)', body, re.IGNORECASE)
        topics_raw = topics_m.group(1).strip() if topics_m else ""
        topics = [t.strip() for t in re.split(r'[,;]', topics_raw) if t.strip()]
        hours  = float(hours_m.group(1)) if hours_m else 2.0

        days.append({
            "day": day_num, "topics": topics, "hours": hours,
            "status": "pending", "focus": "", "questions": "", "flashcards": "",
        })
    return days


# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────

_STATUS_COLORS = {
    "completed":   ("#22c55e", "rgba(34,197,94,0.1)"),
    "in_progress": ("#f59e0b", "rgba(245,158,11,0.1)"),
    "skipped":     ("#888",    "rgba(136,136,136,0.1)"),
    "pending":     ("#3b82f6", "rgba(59,130,246,0.06)"),
}


def _status_badge(status: str) -> str:
    s = status.lower().replace(" ", "_")
    color, bg = _STATUS_COLORS.get(s, ("#888", "rgba(136,136,136,0.1)"))
    return (
        f"<span style='background:{bg};color:{color};"
        f"border:1px solid {color}33;font-size:10px;"
        f"font-weight:600;padding:2px 8px;border-radius:4px;"
        f"font-family:Inter,sans-serif;text-transform:uppercase;'>"
        f"{status.replace('_',' ')}</span>"
    )


def render_study_plan(data: dict,days_remaining: int = None):
    sp_text = data.get("study_plan", "") or ""
    sp_text = re.sub(r"```[a-z]*\n?", "", sp_text).replace("```", "").strip()

    if not sp_text:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No study plan available.</div>",
            unsafe_allow_html=True,
        )
        return

    days = parse_study_plan(sp_text)

    if not days:
        st.warning("Could not parse study plan. Showing raw output below.")
        with st.expander("Raw study plan"):
            st.text(sp_text[:5000])
        return

    # ── Header stats ──
    total_hours = sum(d["hours"] for d in days)
    completed   = sum(1 for d in days if d["status"] == "completed")

    st.markdown(
        f"<div style='display:flex;gap:24px;margin-bottom:28px;flex-wrap:wrap;'>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>TOTAL DAYS</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#fff;margin:0;'>{len(days)}</p></div>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>TOTAL HOURS</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#fff;margin:0;'>{total_hours:.1f}h</p></div>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>COMPLETED</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#22c55e;margin:0;'>{completed}/{len(days)}</p></div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    # ── Days remaining banner —──────────────
    if days_remaining is not None:
        urgency_color = (
            "#ef4444" if days_remaining <= 3
            else "#f59e0b" if days_remaining <= 7
            else "#22c55e"
        )
        st.markdown(
            f"<div style='background:rgba(0,0,0,0.3);"
            f"border:1px solid {urgency_color}33;"
            f"border-radius:8px;padding:10px 16px;margin-bottom:20px;"
            f"display:flex;align-items:center;gap:10px;'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:20px;"
            f"font-weight:700;color:{urgency_color};'>{days_remaining}</span>"
            f"<span style='font-family:Inter,sans-serif;font-size:12px;color:#888;'>"
            f"days until exam</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    # ── Day cards ──
    for day in days:
        day_num = day["day"]
        topics  = day["topics"]
        status  = day["status"]
        color, bg = _STATUS_COLORS.get(
            status.lower().replace(" ", "_"),
            ("#888", "rgba(136,136,136,0.06)")
        )

        st.markdown(
            f"<div style='border:1px solid #2a2a2a;border-radius:10px;"
            f"background:{bg};padding:16px 20px;margin-bottom:8px;'>"
            f"<div style='display:flex;align-items:center;gap:12px;"
            f"margin-bottom:10px;flex-wrap:wrap;'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:13px;"
            f"color:{color};font-weight:700;'>DAY {day_num}</span>"
            f"{_status_badge(status)}"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:11px;"
            f"color:#555;margin-left:auto;'>{day['hours']:.1f}h</span>"
            f"</div>"
            + (
                f"<p style='font-family:Inter,sans-serif;font-size:12px;"
                f"color:#888;margin:0 0 10px 0;font-style:italic;'>{day['focus']}</p>"
                if day["focus"] else ""
            )
            + f"</div>",
            unsafe_allow_html=True,
        )

        # ── Topic checkboxes — KEY uses day_num + topic_index (never topic text) ──
        for ti, topic in enumerate(topics):
            checked = st.checkbox(
                topic,
                key=f"sp_day{day_num}_t{ti}",   # ← day_num + index, never topic text
            )
            # Visual feedback (can't change HTML after render, so just indent)
            if checked:
                st.markdown(
                    f"<p style='font-family:JetBrains Mono,monospace;"
                    f"font-size:10px;color:#22c55e;margin:-8px 0 4px 24px;'>"
                    f"✓ done</p>",
                    unsafe_allow_html=True,
                )

        if day.get("questions"):
            st.markdown(
                f"<p style='font-family:Inter,sans-serif;font-size:12px;"
                f"color:#888;margin:6px 0 0 0;'>"
                f"📝 Practice: {day['questions']}</p>",
                unsafe_allow_html=True,
            )
        if day.get("flashcards"):
            st.markdown(
                f"<p style='font-family:Inter,sans-serif;font-size:12px;"
                f"color:#888;margin:2px 0 8px 0;'>"
                f"🃏 Review: {day['flashcards']}</p>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-bottom:4px;'></div>", unsafe_allow_html=True)