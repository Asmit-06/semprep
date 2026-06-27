import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def parse_cheatsheet(cs_text: str) -> list:
    """
    Canonical format:
        ## TOPIC: OSI Model
        TYPE: concept
        PRIORITY: 3
        CONTENT: The OSI model has 7 layers...
        ---

    Returns list of {topic, entry_type, priority, content}
    """
    if not cs_text:
        return []

    cs_text = re.sub(r"```[a-z]*\n?", "", cs_text).replace("```", "").strip()

    entries = []

    topic_blocks = re.split(r'\n##\s+TOPIC:\s*', cs_text)

    for block in topic_blocks:
        block = block.strip()
        if not block or block.startswith("# "):
            continue

        lines = block.split("\n", 1)
        topic = lines[0].strip()
        body  = lines[1] if len(lines) > 1 else ""

        entry_blocks = re.split(r'\n---+\n?', body)

        for eb in entry_blocks:
            eb = eb.strip()
            if not eb:
                continue
            entry_type = _field(eb, "TYPE")    or "concept"
            priority   = _field(eb, "PRIORITY") or "1"
            content    = _field(eb, "CONTENT")  or eb  # fallback: whole block

            try:
                priority = int(priority)
            except Exception:
                priority = 1

            if content:
                entries.append({
                    "topic":      topic,
                    "entry_type": entry_type,
                    "priority":   priority,
                    "content":    content,
                })

    # Fallback: ## Topic / paragraph format
    if not entries:
        entries = _parse_legacy_cheatsheet(cs_text)

    return entries


def _field(text: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _parse_legacy_cheatsheet(text: str) -> list:
    entries = []
    blocks = re.split(r'\n##\s+(?!TOPIC:)', text)
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        lines = block.split("\n", 1)
        topic   = re.sub(r'[#*]', '', lines[0]).strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        if topic and content:
            entries.append({
                "topic": topic,
                "entry_type": "concept",
                "priority": 1,
                "content": content,
            })
    return entries


# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────

_TYPE_COLORS = {
    "formula":    ("#f59e0b", "rgba(245,158,11,0.1)"),
    "definition": ("#3b82f6", "rgba(59,130,246,0.1)"),
    "example":    ("#8b5cf6", "rgba(139,92,246,0.1)"),
    "concept":    ("#22c55e", "rgba(34,197,94,0.1)"),
}


def _type_badge(entry_type: str) -> str:
    et = entry_type.lower()
    color, bg = _TYPE_COLORS.get(et, ("#888", "rgba(136,136,136,0.1)"))
    return (
        f"<span style='background:{bg};color:{color};"
        f"border:1px solid {color}33;font-size:10px;"
        f"font-weight:600;padding:2px 7px;border-radius:4px;"
        f"font-family:Inter,sans-serif;text-transform:uppercase;'>"
        f"{entry_type}</span>"
    )


def render_cheatsheet(data: dict, weak_topics: list = None):
    cs_text = data.get("cheatsheet", "") or ""
    cs_text = re.sub(r"```[a-z]*\n?", "", cs_text).replace("```", "").strip()

    # Also check cheatsheet_text key (new pipeline writes both)
    if not cs_text:
        cs_text = data.get("cheatsheet_text", "") or ""

    if not cs_text:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No cheatsheet available.</div>",
            unsafe_allow_html=True,
        )
        return

    entries = parse_cheatsheet(cs_text)

    if not entries:
        st.warning("Could not parse cheatsheet. Showing raw output below.")
        with st.expander("Raw cheatsheet"):
            st.text(cs_text[:5000])
        return

    # ── Group by topic ──
    by_topic: dict[str, list] = {}
    for e in entries:
        by_topic.setdefault(e["topic"], []).append(e)

    # ── Sort topics by max priority desc ──
    sorted_topics = sorted(
        by_topic.items(),
        key=lambda kv: max(e["priority"] for e in kv[1]),
        reverse=True,
    )

    # ── Summary bar ──
    st.markdown(
        f"<p style='font-family:Inter,sans-serif;font-size:11px;"
        f"font-weight:600;letter-spacing:1.5px;text-transform:uppercase;"
        f"color:#888;margin:0 0 20px 0;'>"
        f"{len(entries)} entries · {len(by_topic)} topics</p>",
        unsafe_allow_html=True,
    )

    # Normalise weak_topics — never None inside the loop
    _weak = weak_topics or []

    for topic, topic_entries in sorted_topics:
        max_priority = max(e["priority"] for e in topic_entries)

        # Highlight high-priority or weak topics
        highlight = max_priority >= 3 or any(
            w.lower() in topic.lower() for w in _weak
        )
        border_color = "#ef4444" if highlight else "#2a2a2a"
        label_text   = " 🔥 HIGH PRIORITY" if highlight else ""

        with st.expander(
            f"{topic}{label_text}  [{len(topic_entries)} entries]",
            expanded=highlight,
        ):
            for ei, entry in enumerate(
                sorted(topic_entries, key=lambda x: x["priority"], reverse=True)
            ):
                st.markdown(
                    f"<div style='border:1px solid {border_color};"
                    f"border-radius:8px;padding:14px 16px;margin-bottom:10px;"
                    f"background:#141414;'>"
                    f"<div style='display:flex;align-items:center;gap:8px;"
                    f"margin-bottom:10px;'>"
                    f"{_type_badge(entry['entry_type'])}"
                    f"<span style='font-family:JetBrains Mono,monospace;"
                    f"font-size:10px;color:#555;'>priority: {entry['priority']}</span>"
                    f"</div>"
                    f"<p style='font-family:Inter,sans-serif;font-size:14px;"
                    f"color:#e6e6e6;margin:0;line-height:1.7;'>"
                    f"{entry['content']}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )