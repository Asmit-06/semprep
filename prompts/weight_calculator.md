
# Weight Calculator — Score Topics by Exam Importance

## Task
Given extracted PYQ data, calculate a WEIGHT SCORE for every topic.
Weight score = how important this topic is for the exam.

Higher weight = study first. Lower weight = skip if short on time.

## Input Format

```json
{
  "subject": "CN",
  "total_years": 5,
  "topics": [
    {
      "topic": "TCP/IP",
      "appearances": 5,
      "years_appeared": ["2020", "2021", "2022", "2023", "2024"],
      "total_marks": 45,
      "max_marks_seen": 13,
      "units": ["Unit 4"],
      "is_recent": true,
      "is_theoretical_only": false
    }
  ]
}
frequency_score = (unique_years_appeared / total_years) × 10
marks_score = (total_marks_assigned / max_possible_marks) × 10
base_weight = (frequency_score × 0.7) + (marks_score × 0.3)
if is_recent == true: weight += 1.0
if len(units) > 1: weight += 1.0
if is_theoretical_only == true AND appearances <= 2:
    weight -= 2.0
    final_weight = min(10.0, max(1.0, base_weight + boosters + penalties))
Round to 1 decimal place.
CRITICAL   (9-10):  Asked in 4-5 of last 5 years      🔥 Study FIRST
HIGH       (7-8):   Asked in 3 of last 5 years        ⚡ Study SECOND
MEDIUM     (5-6):   Asked in 2 of last 5 years        ⚠️  Study if time
LOW        (1-4):   Asked in 1 or never                ❌ SKIP
CRISIS MODE (1-2 days):  Include ONLY weight ≥ 8.0
FAST MODE   (3-5 days):  Include ONLY weight ≥ 6.0
SMART MODE  (6-10 days): Include ONLY weight ≥ 5.0
{
  "subject": "CN",
  "mode": "smart",
  "threshold": 5.0,
  "topics_analyzed": 45,
  "included_topics": [
    {
      "topic": "TCP/IP",
      "frequency_score": 10.0,
      "marks_score": 4.5,
      "base_weight": 8.35,
      "boosters_applied": ["+1.0 recent appearance"],
      "penalties_applied": [],
      "final_weight": 9.35,
      "priority_band": "CRITICAL",
      "emoji": "🔥",
      "action": "Study First",
      "include_in_prep": true
    },
    {
      "topic": "Routing",
      "frequency_score": 6.0,
      "marks_score": 2.6,
      "base_weight": 5.0,
      "boosters_applied": [],
      "penalties_applied": [],
      "final_weight": 5.0,
      "priority_band": "MEDIUM",
      "emoji": "⚠️",
      "action": "Study if time",
      "include_in_prep": true
    }
  ],
  "skipped_topics": [
    {
      "topic": "Obscure Protocol X",
      "final_weight": 2.5,
      "priority_band": "LOW",
      "emoji": "❌",
      "reason": "Appeared only once, low marks, skip"
    }
  ]
}

