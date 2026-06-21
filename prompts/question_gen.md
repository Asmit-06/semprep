
```markdown
# Question Bank Generator — Build Complete Practice Question Set

## Task
Generate a complete practice question bank combining:
1. Actual PYQ questions (extracted from papers)
2. Predicted questions (based on high-weight topics not in recent PYQs)

## Input Rules

Include questions from:
- ALL weight ≥ 6.0 topics
- Topics from actual PYQs (source: PYQ_YEAR)
- Predicted questions for weight ≥ 6 topics not recently asked (source: PREDICTED)

## Question Selection Rules

### From PYQs: Include EXACTLY as written
- Full question text (no shortening)
- Exact marks shown
- Sub-parts labeled (a, b, c)
- Variants labeled ("attempt any X")
- Don't merge or simplify

### Predicted Questions: Generate for gaps
If a weight ≥ 6.5 topic hasn't appeared in last 2 years:
- Generate 1-2 predicted questions in exam style
- Match typical marks for that topic
- Style must match actual PYQ format
- Mark source as "PREDICTED"

## Model Answer Rules

### Model Answer Must Include:

#### For Definition/Concept Questions:
- Clear definition (first line)
- 2-3 key points explaining concept
- One relevant example
- Why it matters (exam context)

#### For Algorithm Questions:
- Algorithm steps (numbered or pseudocode)
- Trace through example (small dataset)
- Time complexity (Big-O)
- Space complexity
- When to use vs alternatives

#### For Comparison Questions:
- Table or structured comparison
- 4-5 key differences
- When to use each
- Examples of each

#### For Diagram Questions:
- Describe what should be drawn
- Label all components
- Include dimensions/relationships
- Explain significance of each part

#### For Numerical/Proof Questions:
- Show all steps
- Explain each step briefly
- Final answer highlighted
- Units (if applicable)

### Examiner Expectations

Add a field for what examiners specifically reward:

## Output Format (STRICT JSON)

```json
{
  "subject": "CN",
  "question_bank": [
    {
      "id": "CN_Q001",
      "question_text": "What is the OSI model? Explain all 7 layers with at least two examples per layer.",
      "source": "PYQ_2023",
      "year": 2023,
      "topic": "OSI Model",
      "weight": 9.5,
      "marks": 13,
      "question_type": "long_answer",
      "model_answer": {
        "key_points": [
          "OSI = Open Systems Interconnection",
          "7-layer reference model for network communication",
          "Each layer independent, serves layer above",
          "Lower layers handle physical aspects, upper layers handle software"
        ],
        "detailed_answer": "OSI Model has 7 layers:\n\n7. APPLICATION: User applications\n   Examples: HTTP (web), SMTP (email), DNS (name resolution), FTP (file transfer)\n\n6. PRESENTATION: Data formatting\n   Examples: Encryption (SSL), Compression (JPEG), Text encoding (ASCII)\n\n5. SESSION: Dialogue management\n   Examples: Establishing calls, managing conversation flow\n\n4. TRANSPORT: End-to-end communication\n   Examples: TCP (reliable), UDP (fast), Port numbers\n\n3. NETWORK: Routing and logical addressing\n   Examples: IP protocol, ICMP (ping), Routers\n\n2. DATA LINK: Physical addressing and framing\n   Examples: Ethernet, MAC addresses, Switches\n\n1. PHYSICAL: Hardware transmission\n   Examples: Network cables, RJ45 connectors, Signal voltage",
        "example_trace": "When you open a website:\n1. (7) Browser makes HTTP request\n2. (6) HTTP encrypted with SSL\n3. (5) Session established with server\n4. (4) Data split into TCP segments, port 443\n5. (3) IP routing to server's IP\n6. (2) Frames created with MAC addresses\n7. (1) Transmitted as electrical signals",
        "time_complexity": "N/A",
        "space_complexity": "N/A"
      },
      "examiner_tip": "CRITICAL: Draw the 7-layer model as a diagram. Label each layer. Give at least 1-2 examples per layer. If you just list names, you lose 4-5 marks. Examiners want to see understanding, not just memory."
    },
    {
      "id": "CN_Q002",
      "question_text": "TCP uses a 3-way handshake to establish connection. Explain the process with a sequence diagram.",
      "source": "PYQ_2022",
      "year": 2022,
      "topic": "TCP/IP",
      "weight": 9.2,
      "marks": 10,
      "question_type": "long_answer",
      "model_answer": {
        "key_points": [
          "3-way handshake establishes TCP connection",
          "Client initiates with SYN",
          "Server responds with SYN-ACK",
          "Client confirms with ACK"
        ],
        "detailed_answer": "TCP 3-Way Handshake:\n\nStep 1 - SYN (Client → Server):\n  Client sends packet with SYN flag set\n  seq = x (client's sequence number)\n  Server receives: \"Client wants to connect\"\n\nStep 2 - SYN-ACK (Server → Client):\n  Server responds with SYN and ACK flags\n  seq = y (server's sequence number)\n  ack = x+1 (acknowledges client's seq)\n  Client receives: \"Server got your request, here's mine\"\n\nStep 3 - ACK (Client → Server):\n  Client sends packet with ACK flag\n  seq = x+1 (continuing from step 1)\n  ack = y+1 (acknowledges server's seq)\n  Server receives: \"Connection confirmed\"\n\nAfter 3-way handshake:\n- Connection is ESTABLISHED\n- Both sides ready for data transmission\n- Each side knows other is listening",
        "example_trace": "Sequence Diagram:\n\nCLIENT                      SERVER\n  |                           |\n  |-------- SYN (x) --------->|\n  |                           |\n  |<---- SYN-ACK (y,x+1) -----|\n  |                           |\n  |------- ACK (x+1,y+1) ---->|\n  |                           |\n  |--- Data Transfer -------->|\n  |                           |\n\nWhy 3-way and not 2-way?\n- After 2-way: Server doesn't know if client got its response\n- After 3-way: Both sides mutually confirmed",
        "time_complexity": "N/A",
        "space_complexity": "N/A"
      },
      "examiner_tip": "MUST DRAW: Sequence diagram with client-server interaction. Label each packet (SYN, SYN-ACK, ACK). Show sequence and acknowledgment numbers. If no diagram, lose 5+ marks."
    },
    {
      "id": "CN_Q003_PREDICTED",
      "question_text": "Explain Dijkstra's Algorithm for finding shortest path. Trace through a graph with 4 nodes and provide the final shortest path tree.",
      "source": "PREDICTED",
      "year": 2025,
      "topic": "Routing Algorithms",
      "weight": 7.8,
      "marks": 13,
      "question_type": "long_answer",
      "model_answer": {
        "key_points": [
          "Dijkstra's finds shortest path from one source to all nodes",
          "Greedy algorithm: always selects minimum distance node",
          "Uses adjacency matrix or list",
          "Time complexity: O((V+E) log V)"
        ],
        "detailed_answer": "Dijkstra's Algorithm:\n\nInput: Graph, source node\nOutput: Shortest distance to all nodes\n\nAlgorithm:\n1. Initialize distance[source] = 0, all others = ∞\n2. Mark all nodes unvisited\n3. Current = source\n4. While unvisited nodes exist:\n   a. For each neighbor of current:\n      - new_distance = distance[current] + edge_weight\n      - If new_distance < distance[neighbor]:\n        - Update distance[neighbor] = new_distance\n        - Set previous[neighbor] = current\n   b. Mark current as visited\n   c. Select unvisited node with minimum distance\n   d. Current = that node\n5. Shortest distances found in distance[]\n6. Paths found via previous[] array",
        "example_trace": "Graph:\n    A --1-- B\n    |       |\n    4       2\n    |       |\n    C --3-- D\n\nFrom source A:\nIteration 0: distance = [0, ∞, ∞, ∞], current = A\nIteration 1: Update B(1), C(4), current = B\nIteration 2: Update D(3), current = D\nIteration 3: No updates, current = C\n\nFinal:\ndistance[A]=0, distance[B]=1, distance[C]=4, distance[D]=3\nShortest paths: A→B(1), A→B→D(3), A→C(4)",
        "time_complexity": "O((V+E) log V) with min-heap, O(V²) with array",
        "space_complexity": "O(V)"
      },
      "examiner_tip": "Show step-by-step execution with table. Include distance array and previous array at each iteration. Trace through example graph. If no table/trace, lose 5+ marks."
    }
  ]
}
