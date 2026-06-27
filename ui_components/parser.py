import re


def parse_flashcard_text(text):
    """
    Parses format:
        ---
        TOPIC: ...
        FRONT: ...
        BACK: ...
        MEMORY HOOK: ...
        DIFFICULTY: ...
        PYQ: ...
        ---
    """
    if not text:
        return None

    # Clean code fences
    text = re.sub(r"```.*?\n", "", text)
    text = text.replace("```", "").strip()

    cards = []

    # Split by --- separators (one or more dashes, possibly with whitespace)
    blocks = re.split(r'\n\s*-{3,}\s*\n', '\n' + text + '\n')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Need at minimum FRONT and BACK
        if 'FRONT:' not in block.upper() or 'BACK:' not in block.upper():
            continue

        topic_match = re.search(r'TOPIC:\s*(.+)', block, re.IGNORECASE)
        front_match = re.search(r'FRONT:\s*(.+?)(?=\n\s*(?:BACK|MEMORY|DIFFICULTY|PYQ|TOPIC):|\Z)',
                                block, re.IGNORECASE | re.DOTALL)
        back_match = re.search(
            r'BACK:\s*(.+?)(?=\n\s*(?:MEMORY HOOK|DIFFICULTY|PYQ|TOPIC|FRONT):|\Z)',
            block, re.IGNORECASE | re.DOTALL
        )
        memory_match = re.search(
            r'MEMORY HOOK:\s*(.+?)(?=\n\s*(?:DIFFICULTY|PYQ|TOPIC|FRONT|BACK):|\Z)',
            block, re.IGNORECASE | re.DOTALL
        )
        difficulty_match = re.search(
            r'DIFFICULTY:\s*(.+?)(?=\n\s*(?:PYQ|TOPIC|FRONT|BACK|MEMORY):|\Z)',
            block, re.IGNORECASE | re.DOTALL
        )

        topic = topic_match.group(1).strip() if topic_match else "General"
        front = front_match.group(1).strip() if front_match else None
        back = back_match.group(1).strip() if back_match else None
        memory_hook = memory_match.group(1).strip() if memory_match else None
        difficulty = difficulty_match.group(1).strip() if difficulty_match else None

        # Filter out INSUFFICIENT_DATA placeholders
        if memory_hook and "INSUFFICIENT" in memory_hook.upper():
            memory_hook = None

        if front and back:
            cards.append({
                "topic": topic,
                "front": front,
                "back": back,
                "memory_hook": memory_hook,
                "difficulty": difficulty,
                "style": None,
                "weight": 0.0
            })

    return cards if cards else None


def extract_table_from_markdown(markdown_text):
    lines = markdown_text.split('\n')
    table_data = []

    for line in lines:
        if '|' in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) > 1 and not all(set(x) <= set('- ') for x in parts):
                table_data.append(parts)

    return table_data if table_data else None