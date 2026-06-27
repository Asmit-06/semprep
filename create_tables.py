"""
create_tables.py
Creates all SEMPREP tables in the Lemma pod.
Idempotent: skips tables that already exist.
Run once after pod setup, or whenever you add new tables.
"""

from lemma_sdk.openapi_client.models.create_table_request import CreateTableRequest
from lemma_sdk.openapi_client.models.column_schema import ColumnSchema, DatastoreDataType
from lemma_client import get_pod, _items


# ============================================================
# Helper: build a column quickly
# ============================================================
def col(name, type_, required=False, default=None, options=None, description=None):
    kwargs = {"name": name, "type_": type_, "required": required}
    if default is not None:
        kwargs["default"] = default
    if options is not None:
        kwargs["options"] = options
    if description is not None:
        kwargs["description"] = description
    return ColumnSchema(**kwargs)


# ============================================================
# SEMPREP Table Definitions
# ============================================================
TABLES = {
    # ----------------------------------------------------------
    "subjects": [
        col("name", DatastoreDataType.TEXT, required=True, description="Subject name (e.g., DBMS, OS, CN)"),
        col("code", DatastoreDataType.TEXT, description="Subject code if any"),
        col("zip_filename", DatastoreDataType.TEXT, description="Originating ZIP file"),
        col("total_resources", DatastoreDataType.INTEGER, default=0),
        col("status", DatastoreDataType.ENUM,
            options=["pending", "processing", "ready", "error"],
            default="pending"),
    ],

    # ----------------------------------------------------------
    "resources": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("file_name", DatastoreDataType.TEXT, required=True),
        col("file_path", DatastoreDataType.TEXT, required=True),
        col("resource_type", DatastoreDataType.ENUM,
            options=["notes", "pyq", "assignment", "exercise", "syllabus", "unknown"],
            default="unknown"),
        col("page_count", DatastoreDataType.INTEGER, default=0),
        col("extracted_text_length", DatastoreDataType.INTEGER, default=0),
    ],

    # ----------------------------------------------------------
    "pyqs": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("year", DatastoreDataType.TEXT),
        col("question_text", DatastoreDataType.TEXT, required=True),
        col("marks", DatastoreDataType.INTEGER, default=0),
        col("topic", DatastoreDataType.TEXT),
        col("source_file", DatastoreDataType.TEXT),
    ],

    # ----------------------------------------------------------
    "exercises_assignments": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("source_type", DatastoreDataType.ENUM,
            options=["exercise", "assignment"],
            default="exercise"),
        col("question_text", DatastoreDataType.TEXT, required=True),
        col("marks", DatastoreDataType.INTEGER, default=0),
        col("topic", DatastoreDataType.TEXT),
        col("source_file", DatastoreDataType.TEXT),
    ],

    # ----------------------------------------------------------
    "topics": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("topic_name", DatastoreDataType.TEXT, required=True),
        col("weight", DatastoreDataType.FLOAT, default=0.0),
        col("subtopics", DatastoreDataType.JSON, description="List of subtopics"),
        col("frequency", DatastoreDataType.INTEGER, default=0,
            description="How often this topic appears in PYQs"),
    ],

    # ----------------------------------------------------------
    "question_bank": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("question_text", DatastoreDataType.TEXT, required=True),
        col("marks", DatastoreDataType.INTEGER, default=0),
        col("topic", DatastoreDataType.TEXT),
        col("source_type", DatastoreDataType.ENUM,
            options=["pyq", "exercise", "assignment", "ai_generated"],
            default="ai_generated"),
        col("source_reference", DatastoreDataType.TEXT,
            description="Original file or PYQ year"),
        col("answer", DatastoreDataType.TEXT),
        col("keywords", DatastoreDataType.JSON, description="List of marking keywords"),
        col("difficulty", DatastoreDataType.ENUM,
            options=["easy", "medium", "hard"],
            default="medium"),
    ],

    # ----------------------------------------------------------
    "flashcards": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("topic", DatastoreDataType.TEXT),
        col("question", DatastoreDataType.TEXT, required=True),
        col("answer", DatastoreDataType.TEXT, required=True),
    ],

    # ----------------------------------------------------------
    "cheatsheet_entries": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("topic", DatastoreDataType.TEXT, required=True),
        col("entry_type", DatastoreDataType.ENUM,
            options=["definition", "formula", "concept", "mnemonic"],
            default="concept"),
        col("content", DatastoreDataType.TEXT, required=True),
        col("priority", DatastoreDataType.INTEGER, default=0,
            description="Higher = show first in revision"),
    ],

    # ----------------------------------------------------------
    "study_plan": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("day_number", DatastoreDataType.INTEGER, required=True),
        col("date", DatastoreDataType.DATE),
        col("topics", DatastoreDataType.JSON, description="List of topics for the day"),
        col("estimated_hours", DatastoreDataType.FLOAT, default=2.0),
        col("status", DatastoreDataType.ENUM,
            options=["pending", "in_progress", "completed", "skipped"],
            default="pending"),
    ],

    # ----------------------------------------------------------
    "progress": [
        col("subject_name", DatastoreDataType.TEXT, required=True),
        col("topic", DatastoreDataType.TEXT),
        col("confidence", DatastoreDataType.ENUM,
            options=["weak", "medium", "strong"],
            default="medium"),
        col("questions_attempted", DatastoreDataType.INTEGER, default=0),
        col("questions_correct", DatastoreDataType.INTEGER, default=0),
        col("last_reviewed", DatastoreDataType.DATETIME),
    ],
}


# ============================================================
# Main: Create All Tables
# ============================================================
def main():
    pod = get_pod()

    # Get existing tables
    existing = {t.name for t in _items(pod.tables.list())}
    print(f"Existing tables in pod: {existing}\n")

    created = 0
    skipped = 0
    failed = 0

    for table_name, columns in TABLES.items():
        if table_name in existing:
            print(f"  SKIP    {table_name} (already exists)")
            skipped += 1
            continue

        try:
            request = CreateTableRequest(
                name=table_name,
                columns=columns,
                enable_rls=False,  # Shared tables for the whole pod
                primary_key_column="id",
            )
            pod.tables.create(request)
            print(f"  CREATE  {table_name} ({len(columns)} columns)")
            created += 1
        except Exception as e:
            print(f"  ERROR   {table_name}: {type(e).__name__}: {e}")
            failed += 1

    print()
    print(f"Created: {created}  Skipped: {skipped}  Failed: {failed}")
    print(f"\nFinal table count:")
    for t in _items(pod.tables.list()):
        print(f"  - {t.name}")


if __name__ == "__main__":
    main()