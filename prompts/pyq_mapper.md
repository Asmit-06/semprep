# PYQ Mapper — Extract Questions from Exam Papers

## Task
You are analyzing a university exam question paper.
Your job: Extract EVERY question and map it to its canonical topic.

## Input
Raw text extracted from a PYQ paper (via OCR or PDF text extraction).

## Processing Rules

### Extract ALL Questions
- Every numbered question (1, 2, 3...)
- Every sub-part (a, b, c...)
- Every variant ("attempt any X of Y")
- Don't skip or merge questions

### Identify Marks
- From "marks" column if visible
- From question format (10-mark questions typically have X structure)
- Default: assume 2-5 marks for short, 10-13 marks for long
- If unknown: set to null, not zero

### Identify Question Type
- `short_answer`: 1-4 marks (one-line or 3-4 line answer)
- `medium_answer`: 5-8 marks (6-10 line answer)
- `long_answer`: 9+ marks (full page answer, algorithm/diagram required)
- `mcq`: multiple choice (typically 1 mark)
- `unknown`: can't determine

### Map to Canonical Topics
Use this taxonomy for your subject:

#### For CN (Computer Networks):
- OSI Model, TCP/IP Model, Layers
- Routing, Routing Algorithms, RIP, OSPF, BGP
- TCP vs UDP, TCP Features, Flow Control
- IP Addressing, Subnetting, CIDR
- DNS, HTTP, FTP, Email Protocols
- Error Detection, Error Correction, CRC, Hamming
- MAC Protocols, ALOHA, CSMA/CD, Ethernet
- Network Security, Firewall, VPN

#### For C Programming:
- Variables, Data Types, Operators
- Control Flow (if, loops, switch)
- Functions, Recursion, Storage Classes
- Arrays, Strings, Pointers
- Structures, File Handling
- Dynamic Memory Allocation, malloc, free
- Bit Operations

#### For ML (Machine Learning):
- Regression, Linear Regression, Gradient Descent
- Classification, Logistic Regression, Decision Trees
- Random Forests, SVM, KNN, Naive Bayes
- Clustering, K-Means, Hierarchical Clustering
- Neural Networks, Backpropagation
- Dimensionality Reduction, PCA
- Overfitting, Underfitting, Bias-Variance
- Evaluation Metrics, Confusion Matrix, ROC, AUC

#### For Database:
- ER Diagrams, Entity, Relationship, Attributes
- Relational Model, Keys, Constraints
- SQL Queries, SELECT, WHERE, JOIN, GROUP BY
- Normalization, 1NF, 2NF, 3NF, BCNF
- Functional Dependencies, Armstrong's Axioms
- Transactions, ACID, Concurrency Control
- Indexing, B-Tree, Query Optimization

#### For DOS (Design of Systems / Operating Systems):
- Process States, PCB, Context Switching
- CPU Scheduling, FCFS, SJF, Round Robin
- Process Synchronization, Semaphores, Mutex
- Deadlock, Resource Allocation, Banker's Algorithm
- Memory Management, Paging, Virtual Memory
- Page Replacement, FIFO, LRU, Optimal

#### For ITC (Information Theory and Coding):
- Entropy, Information, Redundancy
- Huffman Coding, Shannon-Fano Coding
- Channel Capacity, Bandwidth, SNR
- Error Detection, CRC, Parity, Checksum
- Hamming Code, Linear Block Codes
- Convolutional Codes

#### For Python:
- Data Types, Variables, Operators
- Control Flow, Loops, Conditionals
- Functions, Arguments, Lambda
- Data Structures, Lists, Tuples, Sets, Dicts
- Strings, Formatting, Methods
- File Handling, Exception Handling
- OOP, Classes, Inheritance, Polymorphism
- Modules, Packages

#### For CNS (Cryptography and Network Security):
- Substitution Ciphers, Transposition Ciphers
- DES, 3DES, AES, Encryption
- RSA, Diffie-Hellman, Public Key Crypto
- Hash Functions, MD5, SHA, HMAC
- Digital Signatures, PKI
- Authentication, Kerberos
- Firewalls, IDS, VPN, SSL/TLS

#### For Other Subjects:
- Use course structure and unit names
- If unclear, ask: "what is the main concept this question tests?"

## Output Format (STRICT JSON)

```json
{
  "subject": "CN",
  "year": "2023",
  "semester": "5th",
  "exam_type": "mid_semester",
  "total_marks": 100,
  "questions": [
    {
      "question_id": "Q1",
      "question_text": "What is the OSI model? Explain all 7 layers with functions.",
      "topic": "OSI Model",
      "unit": "Unit 1",
      "marks": 10,
      "question_type": "long_answer"
    },
    {
      "question_id": "Q2a",
      "question_text": "Define routing.",
      "topic": "Routing",
      "unit": "Unit 3",
      "marks": 2,
      "question_type": "short_answer"
    }
  ]
}
PART A — Answer all questions (10 × 2 = 20 marks)
1. What is TCP?
2. Define UDP.
3. Explain the OSI model.

PART B — Answer one from each unit (5 × 13 = 65 marks)
4. a) Explain routing algorithms with example. (13)
   OR
   b) Draw and explain a network topology. (13)

   {
  "subject": "CN",
  "questions": [
    {
      "question_id": "Q1",
      "question_text": "What is TCP?",
      "topic": "TCP/IP",
      "marks": 2,
      "question_type": "short_answer"
    },
    {
      "question_id": "Q4a",
      "question_text": "Explain routing algorithms with example.",
      "topic": "Routing Algorithms",
      "marks": 13,
      "question_type": "long_answer"
    }
  ]
}