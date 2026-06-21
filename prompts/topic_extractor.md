
**Copy-paste this entire content:**

```markdown
# Topic Extractor — Identify Topics in Lecture Notes

## Task
Given lecture notes or study material, extract EVERY distinct topic covered.
Map each topic to canonical topic names (same as in weight_calculator.md).

## Input
- Subject name (CN, ML, C, Database, etc.)
- Raw text from lecture notes/slides/PDF

## Processing Rules

### What is a "Topic"?
A topic is a distinct, examinable concept covered in notes.

Examples:
- NOT: "Chapter 1: Introduction"
- YES: "OSI Model", "TCP/IP", "Routing Algorithms"

- NOT: "Slide 5: Overview"
- YES: "Variables", "Data Types", "Operators"

### Extract ALL Mentioned Topics
- Even if briefly mentioned
- Even if not fully explained
- Even if combined with other topics
- Include both main topics and subtopics

### Assess Coverage Quality
For each topic, rate:
- `high`: Full explanation, examples, diagrams
- `medium`: Partial coverage, main concepts only
- `low`: Just mentioned, no detail

### Check for Exam Relevance
Cross-reference against known PYQ patterns:
- Topic appears in PYQs → mark as "high_exam_relevance"
- Topic doesn't appear in PYQs → mark as "low_exam_relevance"
- Topic never appeared in 5 years → mark as "likely_skip"

### Identify Key Elements
For each topic, extract:
- Key terms / keywords
- Formulas (if any)
- Diagrams referenced
- Examples given
- Algorithms explained

## Output Format (STRICT JSON)

```json
{
  "subject": "CN",
  "total_topics_extracted": 28,
  "topics": [
    {
      "topic": "OSI Model",
      "unit": "Unit 1",
      "coverage_quality": "high",
      "coverage_summary": "All 7 layers explained with functions and protocols",
      "confidence": "high",
      "key_terms": [
        "Physical Layer",
        "Data Link Layer",
        "Network Layer",
        "Transport Layer",
        "Session Layer",
        "Presentation Layer",
        "Application Layer"
      ],
      "formulas": [],
      "has_diagrams": true,
      "diagrams_referenced": ["7-layer model diagram"],
      "examples_given": ["HTTP works at Layer 7", "TCP at Layer 4"],
      "exam_relevance": "high",
      "reason_for_relevance": "Appears in every PYQ, typically 10 marks"
    },
    {
      "topic": "TCP/IP",
      "unit": "Unit 4",
      "coverage_quality": "high",
      "coverage_summary": "TCP features, UDP comparison, 3-way handshake explained",
      "confidence": "high",
      "key_terms": ["TCP", "UDP", "Connection-oriented", "Unreliable", "Handshake"],
      "formulas": [],
      "has_diagrams": true,
      "examples_given": ["HTTP uses TCP", "DNS uses UDP"],
      "exam_relevance": "high",
      "reason_for_relevance": "Asked in 5/5 years, compare questions common"
    },
    {
      "topic": "Obscure Routing Protocol X",
      "unit": "Unit 5",
      "coverage_quality": "low",
      "coverage_summary": "Mentioned briefly, no detail",
      "confidence": "low",
      "key_terms": ["Protocol X"],
      "exam_relevance": "low",
      "reason_for_relevance": "Never appeared in any PYQ, mentions only"
    }
  ]
}
HIGH:
- Full explanation of concept
- Multiple examples
- Visual diagrams
- Algorithms/procedures listed
- Edge cases mentioned
→ Student can answer exam question from these notes

MEDIUM:
- Main concept covered
- 1-2 examples
- Some structure
- Missing some details
→ Student needs to supplement with PYQs

LOW:
- Just mentioned
- No examples
- Minimal explanation
- Incomplete
→ Student needs external sources
HIGH:
- Appears in PYQs (any year)
- Typical marks: 5+ per appearance
- Covered in multiple notes
→ Must study

MEDIUM:
- Appears in some PYQs
- Covered in lecture notes
- But not highest priority
→ Study if time

LOW:
- Never appeared in PYQs
- Mentioned in notes only
- OR pure theory
→ Skip for time-poor students