import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def parse_priority_list(pl_text: str) -> list:
    """
    Canonical format:
        ## ITEM: 1
        TOPIC: Finite Automata
        WEIGHT: 0.85
        BAND: HIGH
        SUBTOPICS: DFA, NFA
        ---

    Returns list of {rank, topic, weight, band, subtopics}
    """
    if not pl_text:
        return []

    pl_text = re.sub(r"```[a-z]*\n?", "", pl_text).replace("```", "").strip()

    items = []

    item_blocks = re.split(r'\n##\s+ITEM:\s*', pl_text)

    for block in item_blocks:
        block = block.strip()
        if not block or block.startswith("# "):
            continue

        lines = block.split("\n", 1)
        try:
            rank = int(lines[0].strip())
        except Exception:
            rank = len(items) + 1

        body = lines[1] if len(lines) > 1 else ""

        topic     = _field(body, "TOPIC")    or ""
        weight    = _field(body, "WEIGHT")   or "0"
        band      = _field(body, "BAND")     or "MEDIUM"
        subtopics = _field(body, "SUBTOPICS") or ""

        try:
            weight = float(weight)
        except Exception:
            weight = 0.0

        subtopic_list = [s.strip() for s in subtopics.split(",") if s.strip()]

        if topic:
            items.append({
                "rank":      rank,
                "topic":     topic,
                "weight":    weight,
                "band":      band.upper(),
                "subtopics": subtopic_list,
            })

    # Fallback: numbered list "1. Topic — HIGH"
    if not items:
        items = _parse_legacy_priority(pl_text)

    return sorted(items, key=lambda x: x["rank"])


def _field(text: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _parse_legacy_priority(text: str) -> list:
    items = []
    for line in text.split("\n"):
        m = re.match(r'^\d+\.\s+(.+?)(?:\s+[—–-]\s+(\w+))?$', line.strip())
        if m:
            items.append({
                "rank":      len(items) + 1,
                "topic":     m.group(1).strip(),
                "weight":    0.0,
                "band":      (m.group(2) or "MEDIUM").upper(),
                "subtopics": [],
            })
    return items


# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────

_BAND_STYLES = {
    "CRITICAL": ("#ef4444", "rgba(239,68,68,0.08)", "rgba(239,68,68,0.2)"),
    "HIGH":     ("#f59e0b", "rgba(245,158,11,0.08)", "rgba(245,158,11,0.2)"),
    "MEDIUM":   ("#22c55e", "rgba(34,197,94,0.08)",  "rgba(34,197,94,0.2)"),
    "LOW":      ("#888",    "rgba(136,136,136,0.08)", "rgba(136,136,136,0.2)"),
}


def _band_badge(band: str) -> str:
    color, bg, border = _BAND_STYLES.get(band, _BAND_STYLES["MEDIUM"])
    return (
        f"<span style='background:{bg};color:{color};"
        f"border:1px solid {border};font-size:10px;"
        f"font-weight:700;padding:2px 8px;border-radius:4px;"
        f"font-family:Inter,sans-serif;'>{band}</span>"
    )


def render_priority_list(data: dict,days_remaining: int = None):
    pl_text = data.get("priority_list", "") or ""
    pl_text = re.sub(r"```[a-z]*\n?", "", pl_text).replace("```", "").strip()

    # Also check weighted_topics as fallback source
    weighted = data.get("weighted_topics", {})

    if not pl_text and not weighted:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No priority list available.</div>",
            unsafe_allow_html=True,
        )
        return

    items = []

    if pl_text:
        items = parse_priority_list(pl_text)

    # Fallback: build from weighted_topics
    if not items and weighted:
        wt_list = weighted.get("weighted_topics") or weighted.get("topics") or []
        items = [
            {
                "rank":      i + 1,
                "topic":     t.get("topic_name") or t.get("name", ""),
                "weight":    float(t.get("weight") or t.get("weightage") or 0),
                "band":      _weight_to_band(float(t.get("weight") or 0)),
                "subtopics": t.get("subtopics", []),
            }
            for i, t in enumerate(
                sorted(wt_list, key=lambda x: float(x.get("weight") or x.get("weightage") or 0), reverse=True)
            )
            if t.get("topic_name") or t.get("name")
        ]

    if not items:
        st.warning("Could not parse priority list. Showing raw output below.")
        with st.expander("Raw priority list"):
            st.text(pl_text[:5000])
        return

    # ── Header ──
    st.markdown(
        f"<p style='font-family:Inter,sans-serif;font-size:11px;"
        f"font-weight:600;letter-spacing:1.5px;text-transform:uppercase;"
        f"color:#888;margin:0 0 20px 0;'>{len(items)} topics ranked by exam weight</p>",
        unsafe_allow_html=True,
    )
    if days_remaining is not None:
        urgency_color = "#ef4444" if days_remaining <= 3 else "#f59e0b" if days_remaining <= 7 else "#22c55e"
        st.markdown(
            f"<div style='background:rgba(0,0,0,0.3);border:1px solid {urgency_color}33;"
            f"border-radius:8px;padding:10px 16px;margin-bottom:20px;"
            f"display:flex;align-items:center;gap:10px;'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:20px;"
            f"font-weight:700;color:{urgency_color};'>{days_remaining}</span>"
            f"<span style='font-family:Inter,sans-serif;font-size:12px;color:#888;'>"
            f"days until exam — prioritize CRITICAL and HIGH topics first</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


    # ── Render items ──
    for item in items:
        band   = item["band"]
        color, bg, border = _BAND_STYLES.get(band, _BAND_STYLES["MEDIUM"])
        weight_pct = min(int(item["weight"] * 100), 100) if item["weight"] <= 1.0 else min(int(item["weight"]), 100)

        subtopics_html = ""
        if item["subtopics"]:
            tags = "".join(
                f"<span style='background:#1a1a1a;color:#888;"
                f"border:1px solid #2a2a2a;font-size:10px;"
                f"padding:2px 6px;border-radius:3px;"
                f"font-family:JetBrains Mono,monospace;margin:2px;'>{s}</span>"
                for s in item["subtopics"]
            )
            subtopics_html = f"<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;'>{tags}</div>"

        st.markdown(
            f"<div style='border:1px solid {border};border-radius:10px;"
            f"background:{bg};padding:16px 20px;margin-bottom:10px;'>"
            f"<div style='display:flex;align-items:center;gap:12px;"
            f"margin-bottom:8px;flex-wrap:wrap;'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:20px;"
            f"font-weight:700;color:{color};min-width:32px;'>#{item['rank']}</span>"
            f"<span style='font-family:Inter,sans-serif;font-size:16px;"
            f"font-weight:600;color:#e6e6e6;flex:1;'>{item['topic']}</span>"
            f"{_band_badge(band)}"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:12px;"
            f"color:#555;margin-left:auto;'>{weight_pct}%</span>"
            f"</div>"
            # Weight bar
            f"<div style='background:#1a1a1a;border-radius:3px;height:3px;"
            f"margin-bottom:{'8px' if subtopics_html else '0'};'>"
            f"<div style='background:{color};width:{weight_pct}%;"
            f"height:100%;border-radius:3px;'></div>"
            f"</div>"
            f"{subtopics_html}"
            f"</div>",
            unsafe_allow_html=True,
        )


def _weight_to_band(weight: float) -> str:
    if weight >= 0.75:   return "CRITICAL"
    elif weight >= 0.50: return "HIGH"
    elif weight >= 0.25: return "MEDIUM"
    else:                return "LOW"