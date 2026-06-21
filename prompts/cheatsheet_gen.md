
```markdown
# Cheat Sheet Generator — Dynamic Last-Minute Study Guide

## Task
Generate a dense, scannable cheat sheet for reading 20 minutes before exam.
This sheet UPDATES based on student progress (weak topics marked).

## Input Rules

### Core Content: Weight ≥ 8.0 Topics (Always Include)
These are CRITICAL topics. Always on cheat sheet regardless of student progress.

### Dynamic Content: Student's Weak Topics (Always Include)
Topics student marked as "weak" during preparation.
These get EXTRA detail and memory hooks.

### Final Cheat Sheet = CRITICAL topics + WEAK topics

## Cheat Sheet Structure

## Content Rules

### Density Rules
- Maximum **600-800 words** total (scannable in 20 mins)
- Bullet points only (no paragraphs)
- No explaining — just facts
- High information density

### Formula Inclusion
- Include all key formulas
- Show units
- One application example per formula
- NO derivation (save space for facts)

### Algorithm Inclusion
- Step 1, 2, 3... (numbered)
- Pseudocode if easier than text
- Time complexity line
- One example trace (small)

### Memory Hooks
- **Mandatory for CRITICAL topics**
- **Mandatory for weak topics**
- Optional for others
- Make them clever, not boring

### Exam Traps
- One per critical topic
- What examiners mark wrong
- Common student mistakes
- How to avoid it

## Output Format (Markdown — NOT JSON)

**Example Output:**

```markdown
# CN — Last-Minute Cheat Sheet
*Generated: June 27, 2025 | Exam in: 1 day | Topics: 12 critical, 3 weak*

---

## 🔥 CRITICAL CONCEPTS

### OSI Model [W:9.5]
7 Layers (bottom to top):
1. Physical: Cables, voltage, bits
2. Data Link: Frames, MAC, Ethernet
3. Network: IP, routing, packets
4. Transport: TCP/UDP, ports, reliability
5. Session: Dialogue, connection mgmt
6. Presentation: Encryption, compression
7. Application: HTTP, SMTP, DNS, FTP

⚠️ **Trap:** Don't confuse "Layer 4 is Transport" with "TCP is Transport". TCP is one of many transport protocols.
💡 **Hook:** "Please Do Not Throw Sausage Pizza Away" = P-D-N-T-S-P-A

### TCP/IP [W:9.2]
**TCP vs UDP:**
| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Yes | No |
| Reliable | Yes | No |
| Speed | Slower | Fast |
| Overhead | 20B header | 8B header |
| Use | HTTP, Email | DNS, Video |

3-Way Handshake: SYN (x) → SYN-ACK (y, x+1) → ACK (x+1, y+1)

⚠️ **Trap:** Don't say "UDP is unreliable so never use it". UDP is DESIGNED for speed; reliability not guaranteed but may work.
💡 **Hook:** "TCP = careful, UDP = careless. Pick based on need."

---

## ⚠️ YOUR WEAK SPOTS

### Routing Algorithms ← YOU MARKED THIS WEAK
**Why you struggle:** Confusing RIP vs OSPF vs BGP
**Key difference:**
- RIP: Distance Vector, max 15 hops, slow
- OSPF: Link State, no hop limit, fast, OSPF preferred
- BGP: Between networks (ISPs), external routing

**Dijkstra (used by OSPF):**
1. Set all distances to ∞ except source (0)
2. Pick unvisited node with min distance
3. Update neighbors: if new_dist < old_dist, update
4. Repeat until all visited

Example (4 nodes):

⚠️ **Common mistake:** Forgetting to mark nodes as visited
⚠️ **Common mistake:** Updating distance without checking neighbor weight

---

## ⚡ HIGH PRIORITY

### Error Detection [W:7.8]
- Parity: 1 extra bit, detects ODD errors only
- CRC: Treats data as polynomial, remainder = error check
- Checksum: Sum of all data bits, overflow wrapped
- Hamming: Detects AND corrects single-bit errors

---

## 📝 FORMULA SHEET

**Entropy:** H = -Σ P(x) log₂(P(x)) [bits per symbol]

**Channel Capacity:** C = B log₂(1 + S/N) [Hartley-Shannon]
- B = bandwidth (Hz)
- S/N = signal-to-noise ratio

**Data Rate:** R = H × frequency [bits per second]

**TCP Window Size:** Determines flow control amount

---

## 🎯 Last 5 Minutes Before Exam

1. **Glance at memory hooks** — Refresh critical definitions
2. **OSI + TCP/IP** — These appear in 80% of exams
3. **Routing algorithms** — If you marked weak, trace one example
4. **Your handwriting** — Write algorithm/diagram legibly (not speed)

---

## 📋 By Question Type

**If Long Answer (10-13 marks):**
- Draw diagram first
- Write 3-4 key points
- Include one example
- Mention time complexity (if algorithm)

**If Short Answer (2-4 marks):**
- One-liner definition
- One-line example
- Done

**If Comparison:**
- Use table format
- 4 clear differences
- When to use each
