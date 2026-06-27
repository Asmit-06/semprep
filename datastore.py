"""
datastore.py
Drop-in replacement for JSON datastore.
Same public API — main.py and workflows.py need zero changes.
All data now lives in Lemma tables.

Caching: @st.cache_data(ttl=300) wraps the three hot read paths.
         Every write calls _invalidate_caches() to flush stale data.
"""

from datetime import datetime
import streamlit as st

from lemma_store import (
    save_subject,
    list_subjects,
    get_subject,
    save_full_analysis,
    load_full_analysis,
    save_markdown_artifact,
    load_markdown_artifact,
)
from lemma_client import get_pod, _items


def _pod():
    return get_pod()


def _records(table: str, filter_dict: dict = None, limit: int = 500) -> list:
    pod = _pod()
    kwargs = {"limit": limit}
    if filter_dict:
        kwargs["filter"] = [
            {"field": k, "op": "eq", "value": v}
            for k, v in filter_dict.items()
        ]
    res = pod.records.list(table, **kwargs)
    return _items(res)


def _row_to_dict(row) -> dict:
    if isinstance(row, dict):
        return row
    if hasattr(row, "to_dict"):
        return row.to_dict()
    return dict(row.__dict__) if hasattr(row, "__dict__") else {}


def _row(table: str, filter_dict: dict) -> dict:
    rows = _records(table, filter_dict, limit=1)
    if not rows:
        return {}
    return _row_to_dict(rows[0])


# ============================================================
# CACHE LAYER
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def _cached_load_subject_data(subject: str) -> dict:
    return load_full_analysis(subject)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_list_subjects() -> list:
    return list_subjects()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_load_progress(subject: str) -> dict:
    """Cache the raw Lemma read. Returns the full progress row dict."""
    import json

    row = _row("progress", {"subject_name": subject})
    if not row:
        return {}

    def _parse(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return []

    return {
        "weak_topics":     _parse(row.get("weak_topics", [])),
        "mastered_topics": _parse(row.get("mastered_topics", [])),
        "skipped_topics":  _parse(row.get("skipped_topics", [])),
        "last_updated":    row.get("last_updated"),
        "_id":             row.get("id"),
    }


def _invalidate_caches(subject: str = None):
    """
    Call after every write. Clears all three caches.
    subject param is accepted for clarity but we always clear all —
    st.cache_data.clear() is the safest cross-version approach.
    """
    _cached_load_subject_data.clear()
    _cached_list_subjects.clear()
    _cached_load_progress.clear()


# ============================================================
# CACHE PRE-WARMER
# Called once on app startup from main.py.
# Fetches all subjects + their data into cache so subject
# switching is instant on first click.
# ============================================================

def prewarm_cache():
    """
    Pre-load all saved subjects into the Streamlit cache.
    Runs once on startup (guarded by session_state in main.py).
    After this, every subject switch is a cache hit — no Lemma API call.
    """
    try:
        subjects = _cached_list_subjects()
        for subj in subjects:
            if subj:
                _cached_load_subject_data(subj)
                _cached_load_progress(subj)
    except Exception:
        pass  # never crash on prewarm failure


# ============================================================
# Subject data
# ============================================================

def save_subject_data(subject: str, analysis_result: dict):
    save_full_analysis(
        subject=subject,
        analysis=analysis_result,
        zip_filename=analysis_result.get("zip_filename", ""),
    )
    _invalidate_caches(subject)


def load_subject_data(subject: str) -> dict:
    return _cached_load_subject_data(subject)


def list_saved_subjects() -> list:
    return _cached_list_subjects()          # ← was calling list_subjects() directly


def delete_subject_data(subject: str):
    from lemma_store import _delete_where

    for table in [
        "topics", "pyqs", "exercises_assignments",
        "question_bank", "flashcards", "cheatsheet_entries",
        "study_plan", "progress",
    ]:
        try:
            _delete_where(table, {"subject_name": subject})
        except Exception:
            pass

    rows = _records("subjects", {"name": subject})
    pod = _pod()
    for r in rows:
        rid = _row_to_dict(r).get("id")
        if rid:
            pod.records.delete("subjects", rid)

    _invalidate_caches(subject)


# ============================================================
# Progress — internal helpers
# ============================================================

def _default_progress(subject: str) -> dict:
    return {
        "subject": subject,
        "weak_topics": [],
        "mastered_topics": [],
        "skipped_topics": [],
        "last_updated": None,
    }


def _load_progress_row(subject: str) -> dict:
    """
    Load progress for internal write operations.
    Uses the cache for reads, but returns the full dict including _id
    so update calls have the record ID.
    """
    cached = _cached_load_progress(subject)
    if not cached:
        return _default_progress(subject)

    return {
        "subject":         subject,
        "weak_topics":     cached.get("weak_topics", []),
        "mastered_topics": cached.get("mastered_topics", []),
        "skipped_topics":  cached.get("skipped_topics", []),
        "last_updated":    cached.get("last_updated"),
        "_id":             cached.get("_id"),
    }


def _save_progress_row(subject: str, progress: dict):
    pod = _pod()
    data = {
        "subject_name":    subject,
        "weak_topics":     progress.get("weak_topics", []),
        "mastered_topics": progress.get("mastered_topics", []),
        "skipped_topics":  progress.get("skipped_topics", []),
        "last_updated":    datetime.now().isoformat(),
    }

    rid = progress.get("_id")
    if rid:
        pod.records.update("progress", rid, data)
    else:
        existing = _row("progress", {"subject_name": subject})
        if existing:
            eid = existing.get("id")
            if eid:
                pod.records.update("progress", eid, data)
                return
        pod.records.create("progress", data)

    _invalidate_caches(subject)


# ============================================================
# Progress — public API
# ============================================================

def load_progress(subject: str) -> dict:
    p = _load_progress_row(subject)
    return {k: v for k, v in p.items() if k != "_id"}


def save_progress(subject: str, progress_data: dict):
    existing = _load_progress_row(subject)
    existing.update(progress_data)
    existing["last_updated"] = datetime.now().isoformat()
    _save_progress_row(subject, existing)


def mark_topic_weak(subject: str, topic_name: str):
    p = _load_progress_row(subject)
    if topic_name not in p["weak_topics"]:
        p["weak_topics"].append(topic_name)
    if topic_name in p["mastered_topics"]:
        p["mastered_topics"].remove(topic_name)
    _save_progress_row(subject, p)


def mark_topic_mastered(subject: str, topic_name: str):
    p = _load_progress_row(subject)
    if topic_name not in p["mastered_topics"]:
        p["mastered_topics"].append(topic_name)
    if topic_name in p["weak_topics"]:
        p["weak_topics"].remove(topic_name)
    _save_progress_row(subject, p)


def mark_topic_skipped(subject: str, topic_name: str):
    p = _load_progress_row(subject)
    if topic_name not in p["skipped_topics"]:
        p["skipped_topics"].append(topic_name)
    _save_progress_row(subject, p)


def get_weak_topics(subject: str) -> list:
    return load_progress(subject).get("weak_topics", [])


# ============================================================
# Sessions
# ============================================================

def save_session(session_data: dict):
    import json

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_markdown_artifact(
        "__sessions__",
        session_id,
        json.dumps(session_data, indent=2),
    )
    return session_id


# ============================================================
# Summary
# ============================================================

def get_all_progress_summary() -> dict:
    subjects = list_saved_subjects()
    summary = {}
    for subject in subjects:
        progress = load_progress(subject)
        data = load_subject_data(subject)
        total_topics = 0
        if data and "weighted_topics" in data:
            wt = data["weighted_topics"]
            if isinstance(wt, dict) and "weighted_topics" in wt:
                total_topics = len(wt["weighted_topics"])
        summary[subject] = {
            "total_topics":   total_topics,
            "weak_count":     len(progress.get("weak_topics", [])),
            "mastered_count": len(progress.get("mastered_topics", [])),
            "skipped_count":  len(progress.get("skipped_topics", [])),
            "last_updated":   data.get("last_updated") if data else None,
        }
    return summary


def init_datastore():
    """No-op. Tables already created via create_tables.py."""
    pass