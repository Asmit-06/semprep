import streamlit as st
import re


# ─────────────────────────────────────────────────────────────
# RENDER  (reads structured tables, not markdown artifacts)
# ─────────────────────────────────────────────────────────────

def render_progress(subject: str, topics_list: list, progress_data: dict):
    """
    Args:
        subject:       subject name string
        topics_list:   list of {topic_name, weight, ...} dicts
        progress_data: dict from load_progress(subject) 
                       shape: {weak_topics: [...], mastered_topics: [...], ...}
    """
    wt_list = topics_list or []

    if not wt_list:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#444;"
            "font-family:Inter,sans-serif;font-size:14px;'>"
            "No topic data available for progress tracking.</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Build status map from load_progress() output ──
    # load_progress returns {weak_topics: [...], mastered_topics: [...]}
    weak_set     = set(progress_data.get("weak_topics",     []))
    mastered_set = set(progress_data.get("mastered_topics", []))
    skipped_set  = set(progress_data.get("skipped_topics",  []))

    # ── State init for button-driven updates ──
    state_key = f"progress_{subject}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {}
    progress_state: dict = st.session_state[state_key]

    # ── Summary metrics ──
    total    = len(wt_list)
    mastered = sum(
        1 for t in wt_list
        if progress_state.get(_safe_key(t), "pending") == "mastered"
        or t.get("topic_name", "") in mastered_set
    )
    weak = sum(
        1 for t in wt_list
        if progress_state.get(_safe_key(t), "pending") == "weak"
        or t.get("topic_name", "") in weak_set
    )
    skipped = sum(
        1 for t in wt_list
        if progress_state.get(_safe_key(t), "pending") == "skipped"
        or t.get("topic_name", "") in skipped_set
    )
    pending = max(0, total - mastered - weak - skipped)
    pct = int((mastered / total) * 100) if total else 0

    st.markdown(
        f"<div style='display:flex;gap:24px;margin-bottom:28px;flex-wrap:wrap;'>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>MASTERED</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#22c55e;margin:0;'>{mastered}</p></div>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>WEAK</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#ef4444;margin:0;'>{weak}</p></div>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>SKIPPED</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#888;margin:0;'>{skipped}</p></div>"
        f"<div><p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#555;margin:0;letter-spacing:1px;'>PENDING</p>"
        f"<p style='font-family:Inter,sans-serif;font-size:24px;font-weight:700;"
        f"color:#3b82f6;margin:0;'>{pending}</p></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Overall progress bar ──
    st.markdown(
        f"<div style='margin-bottom:8px;display:flex;justify-content:space-between;'>"
        f"<span style='font-family:Inter,sans-serif;font-size:12px;color:#888;'>"
        f"Overall mastery</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:12px;"
        f"color:#22c55e;'>{pct}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.progress(pct / 100)
    st.markdown("<div style='margin-bottom:28px;'></div>", unsafe_allow_html=True)

    # ── Per-topic cards ──
    for ti, topic in enumerate(wt_list):
        t_name  = topic.get("topic_name") or topic.get("name") or f"Topic {ti+1}"
        t_key   = _safe_key(topic)

        # Priority: session_state button clicks > saved progress data
        if progress_state.get(t_key):
            current = progress_state[t_key]
        elif t_name in mastered_set:
            current = "mastered"
        elif t_name in weak_set:
            current = "weak"
        elif t_name in skipped_set:
            current = "skipped"
        else:
            current = "pending"

        weight     = float(topic.get("weight") or 0)
        weight_pct = min(int(weight * 100), 100) if weight <= 1.0 else min(int(weight), 100)

        status_color = {
            "mastered": "#22c55e",
            "weak":     "#ef4444",
            "skipped":  "#888",
            "pending":  "#3b82f6",
        }.get(current, "#3b82f6")

        st.markdown(
            f"<div style='border:1px solid #2a2a2a;border-radius:10px;"
            f"padding:14px 18px;margin-bottom:6px;background:#0d0d0d;'>"
            f"<div style='display:flex;align-items:center;gap:10px;"
            f"margin-bottom:6px;flex-wrap:wrap;'>"
            f"<span style='font-family:Inter,sans-serif;font-size:14px;"
            f"font-weight:600;color:#e6e6e6;flex:1;'>{t_name}</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:11px;"
            f"color:{status_color};text-transform:uppercase;'>{current}</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:10px;"
            f"color:#555;'>{weight_pct}%</span>"
            f"</div>"
            f"<div style='background:#1a1a1a;border-radius:2px;height:2px;"
            f"margin-bottom:10px;'>"
            f"<div style='background:{status_color};width:{weight_pct}%;"
            f"height:100%;border-radius:2px;'></div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Mark buttons — keys use index, never topic text
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("✓ Mastered", key=f"prog_master_{subject}_{ti}",
                         use_container_width=True):
                progress_state[t_key] = "mastered"
                st.session_state[state_key] = progress_state
                st.rerun()
        with b2:
            if st.button("⚠ Weak", key=f"prog_weak_{subject}_{ti}",
                         use_container_width=True):
                progress_state[t_key] = "weak"
                st.session_state[state_key] = progress_state
                st.rerun()
        with b3:
            if st.button("— Skip", key=f"prog_skip_{subject}_{ti}",
                         use_container_width=True):
                progress_state[t_key] = "skipped"
                st.session_state[state_key] = progress_state
                st.rerun()
        with b4:
            if st.button("↩ Reset", key=f"prog_reset_{subject}_{ti}",
                         use_container_width=True):
                progress_state.pop(t_key, None)
                st.session_state[state_key] = progress_state
                st.rerun()

        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)


def _safe_key(topic: dict) -> str:
    """Stable dict key for a topic — uses name, never index."""
    name = topic.get("topic_name") or topic.get("name") or ""
    return re.sub(r'\W+', '_', name).lower()