# Flashcard Generator — Create Study Cards (Weight ≥7 Only)

## Task
Generate exam-focused flashcards ONLY for high-weight topics.
Each flashcard = one testable concept, definition, formula, or procedure.

## Input Rules

### Only Process Topics with Weight ≥ 7.0
- Weight 9-10 (CRITICAL): 6-8 flashcards per topic
- Weight 7-8 (HIGH): 4-6 flashcards per topic
- Weight < 7: DO NOT CREATE FLASHCARDS (skip)

### Required Input Data
```json
{
  "subject": "CN",
  "topics_to_flashcard": [
    {
      "topic": "TCP/IP",
      "weight": 9.2,
      "content_summary": "TCP features, connection, flow control",
      "sample_questions": ["Compare TCP and UDP", "Explain 3-way handshake"]
    }
  ]
}
FRONT: "What is OSI Model? Explain all 7 layers."

BACK:
OSI (Open Systems Interconnection) Model = 7-layer reference model.

1. Physical (Layer 1): Cables, signals, bits
2. Data Link (Layer 2): Frames, MAC, Ethernet
3. Network (Layer 3): Packets, IP, Routing
4. Transport (Layer 4): Segments, TCP, UDP, flow control
5. Session (Layer 5): Dialogue, connection management
6. Presentation (Layer 6): Encryption, compression, translation
7. Application (Layer 7): HTTP, SMTP, DNS, FTP

Memory hook: "Please Do Not Throw Sausage Pizza Away"
{
  "subject": "CN",
  "total_topics": 2,
  "total_flashcards": 11,
  "flashcards": [
    {
      "id": "CN_TCP_001",
      "topic": "TCP/IP",
      "weight": 9.2,
      "front": "Compare TCP and UDP in terms of reliability and speed.",
      "back": "TCP = Transmission Control Protocol\n- Connection-oriented (3-way handshake)\n- Reliable (error checking, retransmission)\n- Slower (more overhead)\n- Used by: HTTP, SMTP, FTP\n\nUDP = User Datagram Protocol\n- Connectionless (no setup)\n- Unreliable (no error checking)\n- Fast (less overhead)\n- Used by: DNS, Video streaming, Online games\n\nKey: TCP trades speed for reliability. UDP trades reliability for speed.",
      "memory_hook": "TCP = Careful (reliable). UDP = Careless (fast).",
      "difficulty": "easy",
      "examiner_tip": "Draw comparison table. Don't just list features."
    },
    {
      "id": "CN_TCP_002",
      "topic": "TCP/IP",
      "weight": 9.2,
      "front": "Explain TCP 3-way handshake with a diagram/sequence.",
      "back": "TCP 3-Way Handshake = process to establish connection between client and server.\n\nSteps:\n1. Client sends SYN (synchronization) packet to server (seq=x)\n2. Server responds with SYN-ACK (seq=y, ack=x+1)\n3. Client sends ACK back (seq=x+1, ack=y+1)\n\nAfter step 3: Connection established, data transfer can begin.\n\nWhy 3-way?\n- Step 1: Client tells server \"I want to talk\"\n- Step 2: Server tells client \"I got it, I'm ready\"\n- Step 3: Client tells server \"Got it, let's go\"\n\nWhy not 2-way?\n- 2-way: Server doesn't know if client received its response\n- 3-way: Both sides confirmed (reliable start)",
      "memory_hook": "SYN → SYN-ACK → ACK. Three flags = three steps.",
      "difficulty": "medium",
      "examiner_tip": "Draw sequence diagram. Label each packet with flags and sequence numbers."
    },
    {
      "id": "CN_OSI_001",
      "topic": "OSI Model",
      "weight": 9.5,
      "front": "OSI Model: Name all 7 layers and give one protocol/example per layer.",
      "back": "OSI Model (Open Systems Interconnection):\n\n7. APPLICATION: HTTP, HTTPS, DNS, SMTP, FTP, Telnet\n6. PRESENTATION: Encryption (SSL), Compression, Formatting\n5. SESSION: Establishes, manages, terminates sessions\n4. TRANSPORT: TCP, UDP (end-to-end delivery, flow control)\n3. NETWORK: IP, ICMP, Routing (logical addressing)\n2. DATA LINK: Ethernet, PPP, MAC (physical addressing, frames)\n1. PHYSICAL: Cables, RJ45, Signals (bits, voltage levels)\n\nMemory: Please Do Not Throw Sausage Pizza Away\n(Physical → Data Link → Network → Transport → Session → Presentation → Application)",
      "memory_hook": "PDN TSP A = 7 layers from bottom to top",
      "difficulty": "easy",
      "examiner_tip": "Write layers in order (1-7 or 7-1). Include at least one example per layer."
    }
  ]
}
FRONT: "Explain Dijkstra's Algorithm for shortest path."

BACK:
Dijkstra's Algorithm:
1. Initialize all distances to infinity except start (=0)
2. Mark all nodes unvisited
3. While unvisited nodes exist:
   a. Select unvisited node with minimum distance
   b. For each neighbor of this node:
      - If new distance < old distance: update
   c. Mark current node visited
4. Shortest paths found

Time Complexity: O((V+E) log V) with min-heap
Space Complexity: O(V)

FRONT: "TCP vs UDP comparison."

BACK:
| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Oriented | Less |
| Reliable | Yes | No |
| Order | Guaranteed | Not guaranteed |
| Speed | Slower | Faster |
| Header | 20 bytes | 8 bytes |
| Use | HTTPS, Email | DNS, Streaming |

FRONT: "What is entropy in information theory?"

BACK:
Entropy (H) = -Σ P(x) × log₂(P(x))

Where:
- P(x) = probability of symbol x
- log₂ = binary logarithm (bits)
- Σ = sum over all symbols

Example: Coin flip
- P(heads) = 0.5, P(tails) = 0.5
- H = -(0.5×log₂(0.5) + 0.5×log₂(0.5))
- H = -(0.5×(-1) + 0.5×(-1)) = 1 bit

Higher entropy = more uncertainty = more information
