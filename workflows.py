"""
workflows.py
------------
Orchestrates SEMPREP end-to-end:
  1. Extracts ZIP via file_processor.process_upload()
  2. For each detected subject, calls run_full_lemma_pipeline()
  3. Saves each subject's analysis to Lemma tables
  4. Returns aggregated results in the shape main.py expects

Routes between Lemma agents pipeline and local OpenRouter pipeline
based on the USE_LEMMA environment variable.
"""

import os
import time
import logging
import tempfile
import shutil
from typing import Optional, Callable

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

USE_LEMMA = os.getenv("USE_LEMMA", "false").lower() in ("true", "1", "yes")

# Minimum extracted text length before we bother running agents.
# Anything less is almost certainly an OCR failure or empty PDF.
MIN_TEXT_CHARS = 100


# ============================================================
# Main entry point — called by Streamlit main.py
# ============================================================

def run_full_pipeline(
    zip_path: str,
    days_remaining: int = 14,
    force_rerun: bool = False,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Top-level pipeline.

    Args:
        zip_path:           path to uploaded ZIP file
        days_remaining:     days until exam
        force_rerun:        if True, re-analyze even already-saved subjects
        progress_callback:  optional fn(subject, step, total, message) for UI

    Returns:
        {
            "status": "success" | "error",
            "results": {subject_name: analysis_dict, ...},
            "subjects_processed": [subject_names],
            "errors": {subject_name: error_message, ...},
            "error": str | None,
        }
    """
    from file_processor import process_upload
    from datastore import list_saved_subjects

    # Step 1 — extract ZIP and bucket files by subject
    extract_dir = tempfile.mkdtemp(prefix="semprep_")
    try:
        try:
            subject_buckets = process_upload(zip_path, extract_dir)
        except Exception as e:
            logger.exception("process_upload failed")
            return {
                "status": "error",
                "error": f"Failed to extract ZIP: {e}",
                "results": {},
                "subjects_processed": [],
                "errors": {},
            }

        if not subject_buckets:
            return {
                "status": "error",
                "error": "No files found in ZIP",
                "results": {},
                "subjects_processed": [],
                "errors": {},
            }

        logger.info(
            f"Extracted {len(subject_buckets)} subject buckets: "
            f"{list(subject_buckets.keys())}"
        )

        try:
            already_saved = set(list_saved_subjects()) if not force_rerun else set()
        except Exception as e:
            logger.warning(f"Could not load saved subjects list: {e}")
            already_saved = set()

        results = {}
        errors = {}
        subjects_processed = []

        for subject, file_type_buckets in subject_buckets.items():
            total_files = sum(len(v) for v in file_type_buckets.values())
            if total_files == 0:
                continue

            # For "Unknown" bucket, let the subject_detector agent figure out
            # the real subject from the text. Do NOT skip.
            is_unknown_bucket = (subject == "Unknown")
            if is_unknown_bucket:
                logger.info(
                    f"'Unknown' bucket has {total_files} files — "
                    f"letting subject_detector agent identify"
                )
                subject_hint = None
            else:
                subject_hint = subject

            # Skip if already analyzed and not forcing rerun
            # (only for known subjects — Unknown bucket always runs)
            if (
                subject in already_saved
                and not force_rerun
                and not is_unknown_bucket
            ):
                logger.info(
                    f"Skipping '{subject}' — already analyzed "
                    f"(use force_rerun=True to redo)"
                )
                subjects_processed.append(subject)
                from datastore import load_subject_data
                try:
                    cached = load_subject_data(subject)
                    if cached:
                        results[subject] = cached
                except Exception as e:
                    logger.warning(f"Could not load cached '{subject}': {e}")
                continue

            # Flatten files for this subject into {filename: text}
            extracted_text = _flatten_subject_files(file_type_buckets)
            if not extracted_text:
                errors[subject] = "No usable text extracted from files"
                logger.warning(f"Skipping '{subject}': no usable text")
                continue

            # Skip if total extracted text is too small (likely OCR failure)
            total_chars = sum(len(t) for t in extracted_text.values())
            if total_chars < MIN_TEXT_CHARS:
                errors[subject] = (
                    f"Too little text extracted ({total_chars} chars) — "
                    f"likely OCR failure"
                )
                logger.warning(
                    f"Skipping '{subject}': only {total_chars} chars extracted"
                )
                continue

            logger.info(
                f"Running pipeline for '{subject}' "
                f"({len(extracted_text)} files, {total_chars} chars)"
            )

            try:
                # ── Retry wrapper: up to 2 retries on network timeout ──────
                _pipe_last_err = None
                analysis = None
                for _attempt in range(3):
                    try:
                        analysis = _run_subject_pipeline(
                            subject_hint=subject_hint,
                            extracted_text=extracted_text,
                            days_remaining=days_remaining,
                            progress_callback=lambda step, total, msg, s=subject: (
                                progress_callback(s, step, total, msg)
                                if progress_callback else None
                            ),
                        )
                        break  # success — exit retry loop
                    except Exception as _e:
                        _pipe_last_err = _e
                        _err_str = str(_e)
                        _is_timeout = (
                            "ConnectTimeout" in _err_str
                            or "LemmaTimeout" in _err_str
                            or "10060" in _err_str
                            or "timed out" in _err_str.lower()
                        )
                        if _is_timeout and _attempt < 2:
                            _wait = 15 * (_attempt + 1)
                            print(
                                f"  [retry {_attempt+1}/2] Network timeout on "
                                f"'{subject}', waiting {_wait}s..."
                            )
                            logger.warning(
                                f"Network timeout on '{subject}' "
                                f"(attempt {_attempt+1}/3), retrying in {_wait}s"
                            )
                            time.sleep(_wait)
                        else:
                            # Non-timeout error OR out of retries — bubble up
                            raise
                # ── End retry wrapper ────────────────────────────────────

                # Use the AGENT-DETECTED subject name as storage key.
                # This is critical for the Unknown bucket — the agent may
                # detect that "Unknown" files are actually Computer Networks etc.
                detected_subject = analysis.get("subject") or subject
                if not detected_subject or detected_subject == "Unknown":
                    detected_subject = f"Subject_{len(results) + 1}"

                # If detected name collides with an already-processed subject,
                # merge by keeping the longer/richer analysis (simple heuristic)
                if detected_subject in results:
                    logger.info(
                        f"'{detected_subject}' already processed in this run, "
                        f"appending bucket data"
                    )
                    # For now just overwrite; in a future version we could merge
                    # question_bank, flashcards etc.

                _save_analysis(
                    detected_subject,
                    analysis,
                    zip_filename=os.path.basename(zip_path),
                )

                results[detected_subject] = analysis
                if detected_subject not in subjects_processed:
                    subjects_processed.append(detected_subject)
                logger.info(f"Completed '{detected_subject}'")

            except Exception as e:
                logger.exception(f"Pipeline failed for bucket '{subject}'")
                errors[subject] = str(e)

        return {
            "status": "success" if subjects_processed else "error",
            "results": results,
            "subjects_processed": subjects_processed,
            "errors": errors,
            "error": None if subjects_processed else "No subjects could be analyzed",
        }

    finally:
        # Always clean up extracted temp files
        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception:
            pass


# ============================================================
# Pipeline dispatch (Lemma vs local OpenRouter)
# ============================================================

def _run_subject_pipeline(
    subject_hint: Optional[str],
    extracted_text: dict,
    days_remaining: int,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """Route to Lemma agents or local OpenRouter based on USE_LEMMA flag."""
    if USE_LEMMA:
        from lemma_pipeline import run_full_lemma_pipeline
        return run_full_lemma_pipeline(
            extracted_text=extracted_text,
            days_remaining=days_remaining,
            subject_hint=subject_hint,
            progress_callback=progress_callback,
        )
    else:
        from agent import run_full_analysis
        return run_full_analysis(
            extracted_text=extracted_text,
            days_remaining=days_remaining,
            subject_hint=subject_hint,
            progress_callback=progress_callback,
        )


# ============================================================
# Helpers
# ============================================================

def _flatten_subject_files(file_type_buckets: dict) -> dict:
    """
    Convert {"PYQ": [file_dict, ...], "Notes": [...], ...}
    into {"filename.pdf": "raw_text", ...} for the pipeline.
    Prefixes filename with file_type so agents can see context.
    """
    out = {}
    for file_type, files in file_type_buckets.items():
        for f in files:
            if not isinstance(f, dict):
                continue
            fname = f.get("filename", "unknown.pdf")
            text = f.get("raw_text", "") or ""
            if not text.strip():
                continue
            # Tag filename so agents know its type
            key = f"[{file_type}] {fname}" if file_type != "Unknown" else fname
            out[key] = text
    return out


def _save_analysis(subject: str, analysis: dict, zip_filename: str = ""):
    """Persist analysis to Lemma tables via lemma_store."""
    try:
        from lemma_store import save_full_analysis
        save_full_analysis(subject, analysis, zip_filename=zip_filename)
        logger.info(f"Saved '{subject}' to Lemma tables")
    except Exception as e:
        logger.warning(f"Could not save '{subject}' to Lemma: {e}")


# ============================================================
# Regenerate helpers (called by main.py for tab-level refresh)
# ============================================================

def regenerate_cheatsheet_workflow(subject: str, days_remaining: int = 7) -> dict:
    """
    Re-run only the cheatsheet step for a subject using its existing analysis.
    """
    from datastore import load_subject_data
    from lemma_store import save_markdown_artifact, save_cheatsheet_entries

    data = load_subject_data(subject)
    if not data:
        return {"status": "error", "error": "Subject not found"}

    if USE_LEMMA:
        from lemma_pipeline import step_cheatsheet_writer, _extract_list, _extract_str
        topics = data.get("topics_raw") or _topics_from_analysis(data)
        combined_text = data.get("source_text", "")

        try:
            out = step_cheatsheet_writer(combined_text, subject, topics)
            entries = _extract_list(out, "cheatsheet", "entries", "sections")
            markdown = _extract_str(out, "markdown", "content")

            if entries:
                save_cheatsheet_entries(subject, [
                    {"topic": e.get("topic", ""), "content": e.get("content", "")}
                    for e in entries
                ])

            if markdown:
                save_markdown_artifact(subject, "cheatsheet", markdown)

            return {"status": "success", "entries": entries, "markdown": markdown}
        except Exception as e:
            logger.exception("regenerate_cheatsheet_workflow failed")
            return {"status": "error", "error": str(e)}

    return {"status": "error", "error": "Regenerate only supported with USE_LEMMA=true"}


def regenerate_study_plan_workflow(subject: str, days_remaining: int = 7) -> dict:
    """Re-run only the study planner for a subject."""
    from datastore import load_subject_data
    from lemma_store import save_study_plan

    data = load_subject_data(subject)
    if not data:
        return {"status": "error", "error": "Subject not found"}

    if USE_LEMMA:
        from lemma_pipeline import step_planner, _extract_list
        topics = _topics_from_analysis(data)
        qb_size = _count_qb(data)
        fc_count = _count_flashcards(data)

        try:
            out = step_planner(
                subject=subject,
                topics=topics,
                days_remaining=days_remaining,
                question_bank_size=qb_size,
                flashcard_count=fc_count,
            )
            plan = _extract_list(out, "study_plan", "plan", "days")
            if plan:
                save_study_plan(subject, [
                    {
                        "day_number": d.get("day", 1),
                        "topics": d.get("topics", []),
                        "estimated_hours": d.get("estimated_hours", 2.0),
                        "status": "pending",
                    }
                    for d in plan
                ])
            return {"status": "success", "study_plan": plan}
        except Exception as e:
            logger.exception("regenerate_study_plan_workflow failed")
            return {"status": "error", "error": str(e)}

    return {"status": "error", "error": "Regenerate only supported with USE_LEMMA=true"}


def _topics_from_analysis(data: dict) -> list:
    """Best-effort topic extraction from a cached analysis dict."""
    wt = data.get("weighted_topics", {})
    if isinstance(wt, dict):
        return wt.get("weighted_topics") or wt.get("topics") or []
    if isinstance(wt, list):
        return wt
    return data.get("topics", [])


def _count_qb(data: dict) -> int:
    qb = data.get("question_bank", "")
    if isinstance(qb, list):
        return len(qb)
    if isinstance(qb, str):
        return qb.count("\n") // 2 if qb else 0
    return 0


def _count_flashcards(data: dict) -> int:
    fc = data.get("flashcards", "")
    if isinstance(fc, list):
        return len(fc)
    if isinstance(fc, str):
        return fc.count("\n") // 2 if fc else 0
    return 0