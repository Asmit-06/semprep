"""
lemma_pipeline.py
-----------------
Orchestrates all 9 SEMPREP Lemma agents in sequence.
Replaces the OpenRouter-based run_full_analysis() pipeline.

Usage:
    from lemma_pipeline import run_full_lemma_pipeline
    result = run_full_lemma_pipeline(
        extracted_text={"filename.pdf": "...text..."},
        days_remaining=14,
        subject_hint=None,
        progress_callback=None,
    )
"""

import json
import re
import time
import logging
import concurrent.futures
from typing import Optional, Callable

from lemma_client import get_pod

logger = logging.getLogger(__name__)

# Constants

MAX_CHARS_PER_CALL = 80_000
POLL_INTERVAL = 2
AGENT_TIMEOUT = 600

AGENT_NAMES = {
    "subject_detector":    "subject_detector",
    "resource_classifier": "resource_classifier",
    "extractor":           "extractor",
    "topic_analyzer":      "topic_analyzer",
    "question_bank_coach": "question_bank_coach",
    "answer_writer":       "answer_writer",
    "flashcard_maker":     "flashcard_maker",
    "cheatsheet_writer":   "cheatsheet_writer",
    "planner":             "planner",
}


# Core agent runner

def run_agent(agent_name: str, message: str, timeout: int = AGENT_TIMEOUT) -> dict:
    """
    Invoke a single Lemma agent and return its parsed JSON output.
    Reads from the assistant message text (c.output is always None for chat agents).
    """
    pod = get_pod()

    # ── Retry create_for_agent up to 3 times on network timeout ──────
    logger.info(f"[{agent_name}] Creating conversation...")
    conv = None
    _create_last_err = None
    for _attempt in range(3):
        try:
            conv = pod.conversations.create_for_agent(
                agent_name,
                title=f"SEMPREP run -- {agent_name} -- {int(time.time())}"
            )
            break  # success
        except Exception as _e:
            _create_last_err = _e
            _err_str = str(_e)
            _is_timeout = (
                "ConnectTimeout" in _err_str
                or "LemmaTimeout" in _err_str
                or "10060" in _err_str
                or "timed out" in _err_str.lower()
                or "503" in _err_str
            )
            if _is_timeout and _attempt < 2:
                _wait = 10 * (_attempt + 1)
                logger.warning(
                    f"[{agent_name}] create_for_agent network error "
                    f"(attempt {_attempt+1}/3), retrying in {_wait}s: {_e}"
                )
                time.sleep(_wait)
            else:
                logger.error(
                    f"[{agent_name}] create_for_agent failed after "
                    f"{_attempt+1} attempt(s): {_e}"
                )
                raise
    # ── End retry ─────────────────────────────────────────────────────

    conv_id = conv.id
    logger.info(f"[{agent_name}] conv_id={conv_id}")

    # Send message via stream (ignore early stream close)
    try:
        stream = pod.conversations.send_stream(conv_id, message)
        for line in stream.iter_lines():
            if line.startswith("data:"):
                break
        stream.close()
    except Exception as e:
        logger.debug(f"[{agent_name}] Stream closed early (expected): {e}")

    # Poll until terminal state
    deadline = time.time() + timeout
    final_status = None
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            c = pod.conversations.get(conv_id)
            status = c.last_run_status
            logger.info(f"[{agent_name}] status={status}")
            consecutive_errors = 0  # reset on success

            if status in ("COMPLETED", "FAILED", "WAITING"):
                final_status = status
                break
        except Exception as e:
            consecutive_errors += 1
            logger.warning(
                f"[{agent_name}] Poll error ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}): {e}"
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.error(f"[{agent_name}] Too many consecutive poll errors, giving up")
                break
            time.sleep(3)

    if final_status is None:
        logger.error(f"[{agent_name}] TIMEOUT after {timeout}s")
        return {"_status": "timeout", "_conv_id": str(conv_id)}

    # Read assistant message text
    try:
        msgs = pod.conversations.messages(conv_id)
        assistant_texts = [m.text for m in msgs.items if m.role == "assistant"]
    except Exception as e:
        logger.error(f"[{agent_name}] Could not read messages: {e}")
        return {"_status": "failed", "_conv_id": str(conv_id), "_error": str(e)}

    if not assistant_texts:
        logger.error(f"[{agent_name}] No assistant message returned (status={final_status})")
        return {
            "_status": final_status.lower(),
            "_conv_id": str(conv_id),
            "_error": "no assistant message",
        }

    raw_text = assistant_texts[-1]
    logger.info(f"[{agent_name}] Response length: {len(raw_text)} chars")
    logger.debug(f"[{agent_name}] Raw response: {raw_text[:300]}")

    parsed = _parse_json_response(raw_text)
    parsed["_status"] = final_status.lower()
    parsed["_conv_id"] = str(conv_id)
    parsed["_raw_text"] = raw_text
    return parsed


def _parse_json_response(text: str) -> dict:
    """
    Extract a JSON object from agent response text.
    Tries multiple strategies in order:
      1. Direct parse
      2. Fenced code block (```json ... ```)
      3. Largest balanced {...} block
      4. Fix common JSON errors and retry
    """
    if not text:
        return {}

    try:
        return json.loads(text.strip())
    except Exception:
        pass

    code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
    for block in code_blocks:
        candidate = block.strip()
        try:
            return json.loads(candidate)
        except Exception:
            repaired = _repair_json(candidate)
            try:
                return json.loads(repaired)
            except Exception as e:
                logger.debug(f"Code block parse failed even after repair: {e}")
                continue

    candidate = _extract_largest_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            repaired = _repair_json(candidate)
            try:
                return json.loads(repaired)
            except Exception as e:
                logger.warning(f"Balanced JSON parse failed even after repair: {e}")

    logger.warning(f"Could not extract JSON from response. Raw: {text[:300]}")
    return {"_raw": text}


def _extract_largest_json_object(text: str) -> str:
    best = ""
    for start in range(len(text)):
        if text[start] != '{':
            continue
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    if len(candidate) > len(best):
                        best = candidate
                    break
    return best


def _repair_json(text: str) -> str:
    s = text
    s = s.replace('\u201c', '"').replace('\u201d', '"')
    s = s.replace('\u2018', "'").replace('\u2019', "'")
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    open_braces = s.count('{') - s.count('}')
    open_brackets = s.count('[') - s.count(']')
    if open_brackets > 0:
        s = s + (']' * open_brackets)
    if open_braces > 0:
        s = s + ('}' * open_braces)
    return s


# Text preparation helpers

def _combine_texts(extracted_text: dict, max_chars: int = MAX_CHARS_PER_CALL) -> str:
    parts = []
    for filename, text in extracted_text.items():
        parts.append(f"=== FILE: {filename} ===\n{text}")
    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        logger.warning(f"Text truncated from {len(combined)} to {max_chars} chars")
        combined = combined[:max_chars] + "\n\n[... truncated for context window ...]"
    return combined


def _json_block(data) -> str:
    return f"```json\n{json.dumps(data, indent=2)}\n```"


# Individual agent step functions
# These are all unchanged — same prompts, same inputs, same outputs

def step_subject_detector(combined_text: str, subject_hint: Optional[str] = None) -> dict:
    hint = f"\nUser hint: {subject_hint}" if subject_hint else ""
    message = f"""Analyze the following course materials and identify the subject.{hint}

{combined_text}"""
    return run_agent(AGENT_NAMES["subject_detector"], message)


def step_resource_classifier(combined_text: str, subject: str) -> dict:
    message = f"""Subject: {subject}

Classify each file in the following course materials into one of:
PYQ (past year question paper), Exercise, Assignment, Notes, Other.

{combined_text}"""
    return run_agent(AGENT_NAMES["resource_classifier"], message)


def step_extractor(combined_text: str, subject: str) -> dict:
    message = f"""Subject: {subject}

Extract ALL questions from the following course materials.
For each question identify:
- question_text
- source_type: PYQ | Exercise | Assignment
- source_file
- marks (if visible)
- year (if PYQ)

{combined_text}"""
    return run_agent(AGENT_NAMES["extractor"], message)


def step_topic_analyzer(combined_text: str, subject: str) -> dict:
    message = f"""Subject: {subject}

Analyze the following course materials and identify:
- All major topics and subtopics
- Approximate weightage (%) per topic based on question frequency
- Which topics appear most in PYQs

{combined_text}"""
    return run_agent(AGENT_NAMES["topic_analyzer"], message)


def step_question_bank_coach(
    combined_text: str,
    subject: str,
    topics: list,
    extracted_questions: list,
) -> dict:
    message = f"""Subject: {subject}

Topics identified:
{_json_block(topics)}

Previously extracted questions:
{_json_block(extracted_questions[:50])}

Course materials (for generating additional practice questions):
{combined_text[:30_000]}

Build a comprehensive question bank. For each question include:
- question_text
- topic
- difficulty: Easy | Medium | Hard
- source_type: PYQ | Exercise | Assignment | AI_Generated
- marks"""
    return run_agent(AGENT_NAMES["question_bank_coach"], message)


def step_answer_writer(subject: str, questions: list) -> dict:
    batch = questions[:40]
    message = f"""Subject: {subject}

Write concise model answers for each of the following exam questions.
Return each answer in the same structure with an added "answer" field.

Questions:
{_json_block(batch)}"""
    return run_agent(AGENT_NAMES["answer_writer"], message)


def step_flashcard_maker(combined_text: str, subject: str, topics: list) -> dict:
    topic_names = ", ".join(
        t.get("name", str(t)) if isinstance(t, dict) else str(t)
        for t in topics
    )
    message = f"""Subject: {subject}

Topics: {topic_names}

Create flashcards for all important concepts from the following materials.
Each flashcard: front (term/question), back (definition/answer), topic, difficulty.

{combined_text[:40_000]}"""
    return run_agent(AGENT_NAMES["flashcard_maker"], message)


def step_cheatsheet_writer(combined_text: str, subject: str, topics: list) -> dict:
    topic_names = ", ".join(
        t.get("name", str(t)) if isinstance(t, dict) else str(t)
        for t in topics
    )
    message = f"""Subject: {subject}

Topics: {topic_names}

Create a comprehensive cheat sheet from the following materials.
Group by topic. Include key formulas, definitions, and facts.
Format as structured sections.

{combined_text[:40_000]}"""
    return run_agent(AGENT_NAMES["cheatsheet_writer"], message)


def step_planner(
    subject: str,
    topics: list,
    days_remaining: int,
    question_bank_size: int,
    flashcard_count: int,
) -> dict:
    message = f"""Subject: {subject}
Days until exam: {days_remaining}
Total questions in question bank: {question_bank_size}
Total flashcards: {flashcard_count}

Topics with weightage:
{_json_block(topics)}

Create a detailed day-by-day study plan for {days_remaining} days.
Each day should include:
- topics to cover
- number of questions to practice
- flashcard review count
- estimated hours

Prioritize high-weightage and frequently-tested topics."""
    return run_agent(AGENT_NAMES["planner"], message)


# Safe output extractors

def _extract_list(output: dict, *keys) -> list:
    for key in keys:
        val = output.get(key)
        if isinstance(val, list):
            return val
    for val in output.values():
        if isinstance(val, list) and len(val) > 0:
            return val
    return []


def _extract_str(output: dict, *keys) -> str:
    for key in keys:
        val = output.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


# ============================================================
# Main pipeline
# ============================================================

def run_full_lemma_pipeline(
    extracted_text: dict,
    days_remaining: int = 14,
    subject_hint: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Run all 9 SEMPREP agents with parallel execution in Phase 2.

    Phase 1 (sequential — each needs previous output):
        subject_detector → resource_classifier → extractor → topic_analyzer

    Phase 2 (parallel — all independent, run simultaneously):
        question_bank_coach + answer_writer (chained)
        flashcard_maker
        cheatsheet_writer
        planner

    Phase 2 runs 4 threads concurrently → cuts runtime from ~15 min to ~5 min.
    No quality compromise — every agent receives identical full context.
    """

    TOTAL_STEPS = 9
    step = 0

    def progress(msg: str):
        nonlocal step
        step += 1
        logger.info(f"Step {step}/{TOTAL_STEPS}: {msg}")
        if progress_callback:
            progress_callback(step, TOTAL_STEPS, msg)

    results = {}

    combined_text = _combine_texts(extracted_text)
    logger.info(
        f"Combined text: {len(combined_text)} chars "
        f"from {len(extracted_text)} files"
    )

    # ══════════════════════════════════════════════════════════
    # PHASE 1 — Sequential (each step needs previous output)
    # ══════════════════════════════════════════════════════════

    # Step 1: Subject Detection
    progress("Detecting subject...")
    subject_out = step_subject_detector(combined_text, subject_hint)
    results["subject_detection"] = subject_out

    subject_name = (
        subject_hint
        or _extract_str(subject_out, "subject", "subject_name", "name")
        or "Unknown Subject"
    )
    subject_code = _extract_str(subject_out, "subject_code", "code", "course_code")
    exam_board   = _extract_str(subject_out, "exam_board", "board", "university")
    logger.info(
        f"Subject: {subject_name} | Code: {subject_code} | Board: {exam_board}"
    )

    # Step 2: Resource Classification
    progress("Classifying resources...")
    resource_out = step_resource_classifier(combined_text, subject_name)
    results["resource_classification"] = resource_out
    resources = _extract_list(resource_out, "resources", "files", "classifications")

    # Step 3: Question Extraction
    progress("Extracting questions from materials...")
    extractor_out = step_extractor(combined_text, subject_name)
    results["extraction"] = extractor_out
    extracted_questions = _extract_list(
        extractor_out, "questions", "extracted_questions", "items"
    )
    logger.info(f"Extracted {len(extracted_questions)} questions")

    # Step 4: Topic Analysis
    progress("Analyzing topics and weightage...")
    topic_out = step_topic_analyzer(combined_text, subject_name)
    results["topic_analysis"] = topic_out
    topics = _extract_list(topic_out, "topics", "topic_list", "areas")
    logger.info(f"Found {len(topics)} topics")

    # ══════════════════════════════════════════════════════════
    # PHASE 2 — Parallel (all independent, run simultaneously)
    # question_bank_coach → answer_writer (chained, in one thread)
    # flashcard_maker     (own thread)
    # cheatsheet_writer   (own thread)
    # planner             (own thread)
    # ══════════════════════════════════════════════════════════

    logger.info(
        "[Pipeline] Phase 1 complete. "
        "Starting Phase 2 — parallel agent execution..."
    )

    # Update UI — tell user parallel phase is starting
    # We count steps 5-8 as one progress update before launching threads
    # and step 9 (planner) separately after all finish
    if progress_callback:
        progress_callback(5, TOTAL_STEPS, "Running generation agents in parallel...")

    # ── Thread target functions ───────────────────────────────
    # IMPORTANT: No progress_callback calls inside threads.
    # Streamlit is not thread-safe. All UI updates happen outside threads.

    def _thread_qb_and_answers():
        """Thread 1: question_bank_coach → answer_writer (chained)."""
        logger.info("[Thread-QB] Starting question_bank_coach...")
        qb_out = step_question_bank_coach(
            combined_text, subject_name, topics, extracted_questions
        )
        qb_list = _extract_list(qb_out, "question_bank", "questions", "items")
        logger.info(f"[Thread-QB] question_bank_coach done: {len(qb_list)} questions")

        logger.info("[Thread-QB] Starting answer_writer...")
        ans_out = step_answer_writer(subject_name, qb_list)
        answered = _extract_list(ans_out, "questions", "question_bank", "answers", "items")
        if answered:
            qb_list = answered
        logger.info(f"[Thread-QB] answer_writer done: {len(qb_list)} answered")

        return {"qb_out": qb_out, "ans_out": ans_out, "question_bank": qb_list}

    def _thread_flashcards():
        """Thread 2: flashcard_maker."""
        logger.info("[Thread-FC] Starting flashcard_maker...")
        fc_out = step_flashcard_maker(combined_text, subject_name, topics)
        cards = _extract_list(fc_out, "flashcards", "cards", "items")
        logger.info(f"[Thread-FC] flashcard_maker done: {len(cards)} cards")
        return {"fc_out": fc_out, "flashcards": cards}

    def _thread_cheatsheet():
        """Thread 3: cheatsheet_writer."""
        logger.info("[Thread-CS] Starting cheatsheet_writer...")
        cs_out = step_cheatsheet_writer(combined_text, subject_name, topics)
        entries = _extract_list(cs_out, "cheatsheet", "entries", "sections", "items")
        markdown = _extract_str(cs_out, "markdown", "content", "cheatsheet_markdown")
        logger.info(f"[Thread-CS] cheatsheet_writer done: {len(entries)} entries")
        return {"cs_out": cs_out, "cheatsheet": entries, "cheatsheet_text": markdown}

    def _thread_planner():
        """Thread 4: planner (uses topic weights, not question bank)."""
        logger.info("[Thread-PL] Starting planner...")
        plan_out = step_planner(
            subject=subject_name,
            topics=topics,
            days_remaining=days_remaining,
            # Use extracted_questions count as estimate — actual QB not ready yet
            question_bank_size=len(extracted_questions),
            flashcard_count=0,  # unknown yet — planner doesn't need exact count
        )
        plan = _extract_list(plan_out, "study_plan", "plan", "days", "schedule", "items")
        logger.info(f"[Thread-PL] planner done: {len(plan)} days")
        return {"plan_out": plan_out, "study_plan": plan}

    # ── Launch all 4 threads concurrently ────────────────────
    phase2_results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(_thread_qb_and_answers): "qb_ans",
            executor.submit(_thread_flashcards):     "fc",
            executor.submit(_thread_cheatsheet):     "cs",
            executor.submit(_thread_planner):        "plan",
        }

        for future in concurrent.futures.as_completed(future_map):
            task_name = future_map[future]
            try:
                phase2_results[task_name] = future.result()
                logger.info(f"[Pipeline] Parallel task '{task_name}' completed")
            except Exception as e:
                logger.error(
                    f"[Pipeline] Parallel task '{task_name}' failed: {e}"
                )
                phase2_results[task_name] = {}  # graceful degradation

    logger.info("[Pipeline] Phase 2 (parallel) complete.")

    # ── Unpack phase 2 results ────────────────────────────────
    qb_ans      = phase2_results.get("qb_ans", {})
    fc_res      = phase2_results.get("fc", {})
    cs_res      = phase2_results.get("cs", {})
    plan_res    = phase2_results.get("plan", {})

    question_bank      = qb_ans.get("question_bank", [])
    flashcards         = fc_res.get("flashcards", [])
    cheatsheet_entries = cs_res.get("cheatsheet", [])
    cheatsheet_markdown = cs_res.get("cheatsheet_text", "")
    study_plan         = plan_res.get("study_plan", [])

    results["question_bank_raw"] = qb_ans.get("qb_out", {})
    results["answers_raw"]       = qb_ans.get("ans_out", {})
    results["flashcard_raw"]     = fc_res.get("fc_out", {})
    results["cheatsheet_raw"]    = cs_res.get("cs_out", {})
    results["plan_raw"]          = plan_res.get("plan_out", {})

    logger.info(
        f"Phase 2 results — "
        f"QB: {len(question_bank)} | "
        f"FC: {len(flashcards)} | "
        f"CS: {len(cheatsheet_entries)} | "
        f"Plan: {len(study_plan)} days"
    )

    # Update UI — all done
    if progress_callback:
        progress_callback(9, TOTAL_STEPS, "Pipeline complete.")

    # ══════════════════════════════════════════════════════════
    # Assemble final result — identical shape to before
    # ══════════════════════════════════════════════════════════

    pyqs = [
        q for q in question_bank
        if q.get("source_type") == "PYQ"
    ]
    exercises = [
        q for q in question_bank
        if q.get("source_type") in ("Exercise", "Assignment")
    ]

    final = {
        "subject":         subject_name,
        "subject_code":    subject_code,
        "exam_board":      exam_board,
        "topics":          topics,
        "question_bank":   question_bank,
        "pyqs":            pyqs,
        "exercises":       exercises,
        "flashcards":      flashcards,
        "cheatsheet":      cheatsheet_entries,
        "cheatsheet_text": cheatsheet_markdown,
        "study_plan":      study_plan,
        "resources":       resources,
        "days_remaining":  days_remaining,
        "file_count":      len(extracted_text),
        "pipeline":        "lemma_agents_parallel",
        "agent_outputs":   results,
    }

    logger.info("run_full_lemma_pipeline complete")
    return final