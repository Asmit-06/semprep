import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def parse_flashcards(fc_text: str) -> list:
    """
    Canonical format:
        ## TOPIC: OSI Model
        FRONT: What is layer 2?
        BACK: Data Link Layer
        ---

    Returns flat list of {topic, front, back}
    """
    if not fc_text:
        return []

    fc_text = re.sub(r"```[a-z]*\n?", "", fc_text).replace("```", "").strip()

    cards = []

    # Split on ## TOPIC: lines
    topic_blocks = re.split(r'\n##\s+TOPIC:\s*', fc_text)

    for block in topic_blocks:
        block = block.strip()
        if not block or block.startswith("# "):
            continue

        lines  = block.split("\n", 1)
        topic  = lines[0].strip()
        body   = lines[1] if len(lines) > 1 else ""

        # Each card separated by ---
        card_blocks = re.split(r'\n---+\n?', body)

        for cb in card_blocks:
            cb = cb.strip()
            if not cb:
                continue
            front = _field(cb, "FRONT")
            back  = _field(cb, "BACK")
            if front:
                cards.append({"topic": topic, "front": front, "back": back})

    # Fallback: ## Card N format
    if not cards:
        cards = _parse_legacy_flashcards(fc_text)

    return cards


def _field(text: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _parse_legacy_flashcards(text: str) -> list:
    """Fallback: ## Card N / **Q:** / **A:** format."""
    cards = []
    blocks = re.split(r'\n##\s+Card\s+\d+', text)
    for block in blocks:
        block = block.strip()
        topic_m = re.search(r'\*Topic:\s*(.+?)\*', block)
        topic   = topic_m.group(1).strip() if topic_m else "General"
        q_m = re.search(r'\*\*Q:\*\*\s*(.+?)(?=\n\s*\*\*A:|\Z)', block, re.DOTALL)
        a_m = re.search(r'\*\*A:\*\*\s*(.+?)$', block, re.DOTALL)
        front = re.sub(r'\s+', ' ', q_m.group(1).strip()) if q_m else ""
        back  = re.sub(r'\s+', ' ', a_m.group(1).strip()) if a_m else ""
        if front:
            cards.append({"topic": topic, "front": front, "back": back})
    return cards


# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────

def render_flashcards(data: dict,subject: str = None):
    fc_text = data.get("flashcards", "") or ""
    fc_text = re.sub(r"```[a-z]*\n?", "", fc_text).replace("```", "").strip()

    if not fc_text:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No flashcards available.</div>",
            unsafe_allow_html=True,
        )
        return

    cards = parse_flashcards(fc_text)

    if not cards:
        st.warning("Could not parse flashcards. Showing raw output below.")
        with st.expander("Raw flashcards"):
            st.text(fc_text[:5000])
        return

    # ── Topic filter ──
    topics = ["All"] + sorted(set(c["topic"] for c in cards if c["topic"]))

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_topic = st.selectbox(
            "Filter by topic",
            topics,
            label_visibility="collapsed",
            key="fc_topic_filter",
        )
    with col2:
        st.markdown(
            f"<div style='text-align:right;padding-top:8px;"
            f"font-family:JetBrains Mono,monospace;font-size:12px;color:#555;'>"
            f"{len(cards)} cards</div>",
            unsafe_allow_html=True,
        )

    filtered = cards if selected_topic == "All" else [
        c for c in cards if c["topic"] == selected_topic
    ]

    if not filtered:
        st.info("No cards for this topic.")
        return

    # ── Card navigator state ──
    if "fc_index" not in st.session_state:
        st.session_state.fc_index = 0
    if "fc_flipped" not in st.session_state:
        st.session_state.fc_flipped = False

    # Reset if out of bounds
    if st.session_state.fc_index >= len(filtered):
        st.session_state.fc_index = 0
        st.session_state.fc_flipped = False

    idx   = st.session_state.fc_index
    card  = filtered[idx]
    flipped = st.session_state.fc_flipped

    # ── Progress bar ──
    progress = (idx + 1) / len(filtered)
    st.markdown(
        f"<div style='background:#1a1a1a;border-radius:4px;height:3px;"
        f"margin-bottom:24px;overflow:hidden;'>"
        f"<div style='background:#3b82f6;width:{progress*100:.1f}%;"
        f"height:100%;border-radius:4px;transition:width 0.3s;'></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Card face ──
    if not flipped:
        face_bg    = "#0f172a"
        face_label = "FRONT"
        face_color = "#3b82f6"
        face_text  = card["front"]
        hint       = "Click 'Flip' to reveal the answer"
    else:
        face_bg    = "#0a140a"
        face_label = "BACK"
        face_color = "#22c55e"
        face_text  = card["back"] or "No answer recorded."
        hint       = ""

    topic_badge = (
        f"<span style='background:rgba(59,130,246,0.1);color:#3b82f6;"
        f"border:1px solid rgba(59,130,246,0.2);font-size:10px;"
        f"font-weight:600;padding:2px 8px;border-radius:4px;"
        f"font-family:Inter,sans-serif;'>{card['topic']}</span>"
        if card["topic"] else ""
    )

    st.markdown(
        f"<div style='background:{face_bg};border:1px solid #2a2a2a;"
        f"border-radius:12px;padding:40px 32px;min-height:180px;"
        f"display:flex;flex-direction:column;align-items:center;"
        f"justify-content:center;text-align:center;margin-bottom:16px;'>"
        f"<p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:{face_color};letter-spacing:2px;margin:0 0 20px 0;'>"
        f"// {face_label}</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:17px;"
        f"font-weight:500;color:#e6e6e6;margin:0 0 20px 0;line-height:1.6;'>"
        f"{face_text}</p>"
        f"{topic_badge}"
        f"{'<p style=\"font-family:Inter,sans-serif;font-size:11px;color:#555;margin:16px 0 0 0;\">' + hint + '</p>' if hint else ''}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Controls ──
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])

    with c1:
        if st.button("◀ Prev", key="fc_prev", use_container_width=True):
            st.session_state.fc_index   = (idx - 1) % len(filtered)
            st.session_state.fc_flipped = False
            st.rerun()

    with c2:
        if st.button("▶ Next", key="fc_next", use_container_width=True):
            st.session_state.fc_index   = (idx + 1) % len(filtered)
            st.session_state.fc_flipped = False
            st.rerun()

    with c3:
        label = "🔒 Hide Answer" if flipped else "🔓 Flip"
        if st.button(label, key="fc_flip", use_container_width=True):
            st.session_state.fc_flipped = not flipped
            st.rerun()

    with c4:
        if st.button("↩ Reset", key="fc_reset", use_container_width=True):
            st.session_state.fc_index   = 0
            st.session_state.fc_flipped = False
            st.rerun()

    with c5:
        st.markdown(
            f"<div style='text-align:center;padding-top:6px;"
            f"font-family:JetBrains Mono,monospace;font-size:12px;color:#555;'>"
            f"{idx + 1} / {len(filtered)}</div>",
            unsafe_allow_html=True,
        )

    # ── All cards list (collapsed) ──
    with st.expander(f"View all {len(filtered)} cards", expanded=False):
        for ci, c in enumerate(filtered):
            st.markdown(
                f"<div style='border:1px solid #2a2a2a;border-radius:8px;"
                f"padding:12px 16px;margin-bottom:8px;'>"
                f"<p style='font-family:JetBrains Mono,monospace;font-size:10px;"
                f"color:#3b82f6;margin:0 0 6px 0;'>CARD {ci+1} · {c['topic']}</p>"
                f"<p style='font-family:Inter,sans-serif;font-size:13px;"
                f"color:#e6e6e6;margin:0 0 4px 0;font-weight:500;'>{c['front']}</p>"
                f"<p style='font-family:Inter,sans-serif;font-size:12px;"
                f"color:#888;margin:0;'>{c['back']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )