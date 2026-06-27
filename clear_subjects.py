"""
clear_subjects.py
Deletes specific subjects (and all related data) from Lemma tables.

Usage:
    python clear_subjects.py "Computer Networks"
    python clear_subjects.py "Computer Networks" "DOS" "C" "CN"
    python clear_subjects.py --all
"""

import sys
from datastore import delete_subject_data, list_saved_subjects


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print('  python clear_subjects.py "Subject Name"')
        print('  python clear_subjects.py "Subject A" "Subject B"')
        print("  python clear_subjects.py --all")
        return

    if args[0] == "--all":
        subjects = list_saved_subjects()
        if not subjects:
            print("No subjects to delete.")
            return
        print(f"Found {len(subjects)} subjects: {subjects}")
        confirm = input("Delete ALL? Type YES to confirm: ").strip()
        if confirm != "YES":
            print("Cancelled.")
            return
        targets = subjects
    else:
        targets = args

    for subject in targets:
        print(f"Deleting '{subject}'...")
        try:
            delete_subject_data(subject)
            print(f"  Deleted.")
        except Exception as e:
            print(f"  Failed: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()