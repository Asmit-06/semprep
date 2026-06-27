try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import streamlit as st
from workflows import run_full_pipeline, regenerate_cheatsheet_workflow, regenerate_study_plan_workflow
from datastore import list_saved_subjects, load_subject_data, load_progress
from ui_components import priority_list, question_bank, flashcards, study_plan, cheatsheet, progress

st.set_page_config(page_title="SEMPREP", layout="wide")

st.markdown("""
<style>



/* ── Dark mode (default) ── */
:root {
    --lambo-gold:        #FFC000;
    --lambo-gold-dark:   #917300;
    --lambo-gold-text:   #FFCE3E;
    --lambo-cyan:        #29ABE2;
    --lambo-teal:        #1EAEDB;
    --lambo-link:        #3860BE;
    --lambo-steel:       #969696;
    --lambo-ash:         #7D7D7D;

    /* Semantic surface tokens — dark */
    --bg-page:           #000000;
    --bg-card:           #202020;
    --bg-deep:           #181818;
    --bg-sidebar:        #181818;
    --bg-hover:          #2a2a2a;

    /* Text tokens — dark */
    --text-primary:      #FFFFFF;
    --text-secondary:    #F5F5F5;
    --text-muted:        #7D7D7D;
    --text-micro:        #969696;

    /* Border tokens — dark */
    --border-subtle:     rgba(255,255,255,0.10);
    --border-gold:       rgba(255,192,0,0.30);
    --border-active:     #FFC000;

    /* Button tokens */
    --btn-cta-bg:        #FFC000;
    --btn-cta-fg:        #000000;
    --btn-cta-hover:     #917300;
    --btn-ghost-border:  rgba(255,255,255,0.45);
    --btn-ghost-hover:   rgba(30,174,219,0.65);
}

/* ── Light mode overrides ── */
@media (prefers-color-scheme: light) {
    :root {
        --bg-page:          #F8F8F8;
        --bg-card:          #FFFFFF;
        --bg-deep:          #EDEDED;
        --bg-sidebar:       #F0F0F0;
        --bg-hover:         #E6E6E6;

        --text-primary:     #000000;
        --text-secondary:   #202020;
        --text-muted:       #494949;
        --text-micro:       #666666;

        --border-subtle:    rgba(0,0,0,0.10);
        --border-gold:      rgba(145,115,0,0.25);
        --border-active:    #917300;

        --btn-ghost-border: rgba(0,0,0,0.30);
        --btn-ghost-hover:  rgba(30,174,219,0.15);
    }
}

/* ── Streamlit also injects its own dark attribute ── */
[data-theme="dark"] {
    --bg-page:       #000000;
    --bg-card:       #202020;
    --bg-deep:       #181818;
    --bg-sidebar:    #181818;
    --bg-hover:      #2a2a2a;
    --text-primary:  #FFFFFF;
    --text-secondary:#F5F5F5;
    --text-muted:    #7D7D7D;
    --text-micro:    #969696;
    --border-subtle: rgba(255,255,255,0.10);
}

[data-theme="light"] {
    --bg-page:       #F8F8F8;
    --bg-card:       #FFFFFF;
    --bg-deep:       #EDEDED;
    --bg-sidebar:    #F0F0F0;
    --bg-hover:      #E6E6E6;
    --text-primary:  #000000;
    --text-secondary:#202020;
    --text-muted:    #494949;
    --text-micro:    #666666;
    --border-subtle: rgba(0,0,0,0.10);
}

/* ══ GLOBAL BASE ══ */
.stApp {
    background: var(--bg-page) !important;
    font-family: 'Inter', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}

.main .block-container {
    padding-top: 1rem;
    max-width: 1440px;
}

/* ══ HERO HEADER ══ */
.lambo-header {
    background: var(--bg-page);
    padding: 44px 32px 36px;
    text-align: center;
    margin-bottom: 28px;
    border-bottom: 2px solid var(--lambo-gold);
    position: relative;
}

.lambo-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--lambo-gold);
}

.lambo-header h1 {
    color: var(--text-primary);
    font-size: 48px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 10px;
    margin: 0;
    line-height: 1.0;
}

.lambo-header h1 span {
    color: var(--lambo-gold);
}

.lambo-header .tagline {
    color: var(--lambo-gold);
    font-size: 11px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 5px;
    margin-top: 12px;
}

/* ══ SIDEBAR ══ */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-subtle);
}

section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

.lambo-sidebar-brand {
    text-align: center;
    padding: 28px 12px 24px;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 20px;
}

.lambo-sidebar-brand h2 {
    color: var(--lambo-gold);
    font-size: 20px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 5px;
    margin: 0;
}

.lambo-sidebar-brand p {
    color: var(--text-micro);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin: 8px 0 0;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--lambo-gold) !important;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    font-size: 12px !important;
    font-weight: 600;
}

.lambo-hint {
    color: var(--text-micro);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    line-height: 1.6;
    margin-bottom: 16px;
}

/* ══ DASHBOARD MINI CARD (sidebar) ══ */
.lambo-dash-card {
    background: var(--bg-page);
    border: 1px solid var(--border-subtle);
    border-top: 2px solid var(--lambo-gold);
    padding: 16px;
    margin-bottom: 16px;
}

.lambo-dash-card h4 {
    color: var(--lambo-gold);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-weight: 600;
    margin: 0 0 12px;
}

.lambo-dash-card p {
    color: var(--text-muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 4px 0;
}

.lambo-dash-card .dash-value {
    color: var(--text-primary);
    font-size: 20px;
    font-weight: 400;
    margin: 0;
}

/* ══ BUTTONS ══ */
/* Gold CTA — primary */
.stButton button[kind="primary"] {
    background: var(--btn-cta-bg) !important;
    color: var(--btn-cta-fg) !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 12px 24px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 2.5px !important;
    transition: background 0.2s ease !important;
}

.stButton button[kind="primary"]:hover {
    background: var(--btn-cta-hover) !important;
    color: var(--lambo-white, #FFF) !important;
}

/* Ghost — secondary */
.stButton > button {
    background: transparent !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--btn-ghost-border) !important;
    border-radius: 0 !important;
    padding: 10px 18px !important;
    font-size: 11px !important;
    font-weight: 400 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    transition: border-color 0.2s, color 0.2s !important;
}

.stButton > button:hover {
    border-color: var(--lambo-gold) !important;
    color: var(--lambo-gold) !important;
    background: var(--btn-ghost-hover) !important;
}

/* ══ METRIC CARDS ══ */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: 2px solid var(--lambo-gold) !important;
    border-radius: 0 !important;
    padding: 20px 16px !important;
    transition: border-color 0.2s;
}

div[data-testid="metric-container"]:hover {
    border-top-color: var(--lambo-gold-dark) !important;
}

div[data-testid="metric-container"] label {
    color: var(--text-micro) !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    font-weight: 600;
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 30px !important;
    font-weight: 300 !important;
    line-height: 1.1 !important;
}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent;
    padding: 12px 22px !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-size: 11px;
    font-weight: 600;
    transition: color 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--lambo-gold) !important;
    background: var(--bg-hover) !important;
}

.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--lambo-gold) !important;
    border-bottom: 2px solid var(--lambo-gold) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px;
}

/* ══ PROGRESS BAR ══ */
.stProgress > div > div {
    background: var(--border-subtle) !important;
    border-radius: 0 !important;
    height: 3px !important;
}

.stProgress > div > div > div > div {
    background: var(--lambo-gold) !important;
    border-radius: 0 !important;
}

/* ══ ALERTS / STATUS ══ */
div[data-testid="stAlert"] {
    border-radius: 0 !important;
    border-left-width: 3px !important;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ══ FORM ELEMENTS ══ */
[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed var(--border-subtle) !important;
    border-radius: 0 !important;
    background: var(--bg-card) !important;
}

.stNumberInput input,
.stTextInput input {
    border-radius: 0 !important;
    border-color: var(--border-subtle) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
}

[data-testid="stSelectbox"] > div > div {
    border-radius: 0 !important;
    border-color: var(--border-subtle) !important;
    background: var(--bg-card) !important;
}

/* ══ DIVIDER ══ */
hr {
    border-color: var(--border-subtle) !important;
    border-top-width: 1px !important;
}

/* ══ HEADINGS inside main content ══ */
h1, h2, h3 {
    text-transform: uppercase;
    letter-spacing: 3px;
    font-weight: 400 !important;
}

/* ══ SUBJECT TITLE ══ */
.lambo-subject-title {
    font-size: 28px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 6px;
    color: var(--text-primary);
    border-left: 3px solid var(--lambo-gold);
    padding-left: 16px;
    margin-bottom: 24px;
    line-height: 1.1;
}

/* ══ READINESS ROW ══ */
.lambo-readiness-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--text-micro);
    margin-bottom: 6px;
    margin-top: 8px;
}

/* ══ EMPTY STATE ══ */
.lambo-empty {
    text-align: center;
    padding: 80px 40px;
}

.lambo-empty .icon {
    font-size: 48px;
    margin-bottom: 20px;
}

.lambo-empty .label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 5px;
    color: var(--text-muted);
}

/* ══ SPINNER ══ */
div[data-testid="stSpinner"] svg {
    stroke: var(--lambo-gold) !important;
}

/* ══ CHECKBOX ══ */
.stCheckbox label span {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted) !important;
}

</style>
""", unsafe_allow_html=True)


# ── HERO HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="lambo-header">
    <h1><span>SEM</span>PREP</h1>
    <div class="tagline">STOP SORTING START STUDYING</div>
</div>
""", unsafe_allow_html=True)


# ── SESSION STATE ────────────────────────────────────────────────────────────
if "current_results" not in st.session_state:
    st.session_state.current_results = {}
if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = None

if "cache_warmed" not in st.session_state:
     from datastore import prewarm_cache
     prewarm_cache()
     st.session_state.cache_warmed = True


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<span class="section-label">Upload & Settings</span>', unsafe_allow_html=True)
    uploaded_zip = st.file_uploader("Upload ZIP", type=["zip"], label_visibility="collapsed")
    days_remaining = st.number_input("Days until exam", min_value=1, max_value=30, value=5)
    force_rerun = st.checkbox("Force re-analysis")

    if days_remaining <= 2:
        mode = "CRISIS MODE"
    elif days_remaining <= 5:
        mode = "FAST MODE"
    else:
        mode = "SMART MODE"

    st.markdown(f"""
    <div style='margin: 12px 0;'>
        <span class='section-label'>Current Mode</span>
        <span class='priority-badge {"badge-critical" if days_remaining <= 2 else "badge-high" if days_remaining <= 5 else "badge-medium"}'>{mode}</span>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_zip:
        temp_zip_path = "temp_uploaded.zip"
        with open(temp_zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        if st.button("Run Analysis", use_container_width=True):
            status_box = st.status("Starting analysis...", expanded=True)

            def progress_cb(subject, step, total, message):
                status_box.update(
                    label=f"[{subject}] Step {step}/{total}: {message}",
                    state="running",
                )
                status_box.write(f"[{subject}] Step {step}/{total}: {message}")

            try:
                result = run_full_pipeline(
                    temp_zip_path,
                    days_remaining,
                    force_rerun=force_rerun,
                    progress_callback=progress_cb,
                )

                if result["status"] == "success":
                    st.session_state.current_results = result["results"]
                    subjects_found = result.get("subjects_processed", [])
                    status_box.update(
                        label=f"Done. Analyzed: {', '.join(subjects_found)}",
                        state="complete",
                        expanded=False,
                    )
                    if result.get("errors"):
                        for subj, err in result["errors"].items():
                            st.warning(f"{subj}: {err}")
                else:
                    status_box.update(
                        label=result.get("error", "Something went wrong"),
                        state="error",
                    )
            except Exception as e:
                status_box.update(label=f"Pipeline crashed: {e}", state="error")
                st.exception(e)

    st.markdown('<hr style="border-color: #2a2a2a; margin: 20px 0;">', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Saved Subjects</span>', unsafe_allow_html=True)

with st.sidebar:
    saved = list_saved_subjects()
    # De-duplicate while preserving order
    seen = set()
    saved_unique = []
    for s in saved:
        if s and s not in seen:
            seen.add(s)
            saved_unique.append(s)

    if saved_unique:
        for idx, subj in enumerate(saved_unique):
            if st.button(
                subj,
                use_container_width=True,
                key=f"saved_{idx}_{subj}",
            ):
                st.session_state.selected_subject = subj
    else:
        st.markdown(
            '<p style="color:#5a5a5a;font-size:13px;">No saved subjects yet</p>',
            unsafe_allow_html=True,
        )


# ── AUTO-SELECT FIRST SUBJECT AFTER ANALYSIS ─────────────────────────────────
if st.session_state.current_results:
    subjects = list(st.session_state.current_results.keys())
    if subjects and st.session_state.selected_subject not in subjects:
        st.session_state.selected_subject = subjects[0]

# ── MAIN CONTENT ─────────────────────────────────────────────────────────────
if st.session_state.selected_subject:
    subject = st.session_state.selected_subject
    data    = load_subject_data(subject)

    if not data:
        st.error("No data found for this subject.")
    else:
        weighted_topics = data.get("weighted_topics", {})
        topics_list = []

        if isinstance(weighted_topics, dict):
            topics_list = (
                weighted_topics.get("weighted_topics")
                or weighted_topics.get("topics")
                or []
            )
        elif isinstance(weighted_topics, list):
            topics_list = weighted_topics

        # Subject heading
        st.markdown(
            f'<div class="lambo-subject-title">{subject}</div>',
            unsafe_allow_html=True,
        )

        # ── METRIC ROW ──
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Topics",       len(topics_list))
        col2.metric("Critical",     sum(1 for t in topics_list if t.get("weight", 0) >= 9))
        col3.metric("High Priority", sum(1 for t in topics_list if 7 <= t.get("weight", 0) < 9))
        col4.metric("Weak Areas",   len(load_progress(subject).get("weak_topics", [])))

        # ── READINESS ──
        weak_count    = len(load_progress(subject).get("weak_topics", []))
        total_topics  = max(len(topics_list), 1)
        readiness     = max(0, 100 - int((weak_count / total_topics) * 100))

        if readiness >= 80:
            st.success(f"📈 {readiness}% Ready for Exam")
        elif readiness >= 50:
            st.warning(f"📈 {readiness}% Ready — Keep Going")
        else:
            st.error(f"📈 {readiness}% Ready — Focus Required")

        st.markdown(
            '<div class="lambo-readiness-label">Exam Readiness</div>',
            unsafe_allow_html=True,
        )
        st.progress(readiness / 100)
        st.divider()

        # ── TABS ──
        tabs = st.tabs([
            "Priority",
            "Questions",
            "Flashcards",
            "Study Plan",
            "Cheat Sheet",
            "Progress",
        ])

        with tabs[0]:
            priority_list.render_priority_list(data, days_remaining)

        with tabs[1]:
            question_bank.render_question_bank(data)

        with tabs[2]:
            flashcards.render_flashcards(data, subject)

        with tabs[3]:
            study_plan.render_study_plan(data, days_remaining)

        with tabs[4]:
            cheatsheet.render_cheatsheet(data, load_progress(subject).get("weak_topics", []))

        with tabs[5]:
            progress.render_progress(subject, topics_list, load_progress(subject))

else:
    # ── EMPTY STATE ──
    st.markdown("""
    <div class="lambo-empty">
        <div class="icon">📚</div>
        <div class="label">Select a subject from the sidebar to begin</div>
    </div>
    """, unsafe_allow_html=True)