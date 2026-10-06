---
name: phishing-ai-engineering
description: Builds and teaches the AI Phishing Risk & Security Triage Platform using production-minded software engineering, classical ML, NLP, RAG, LangGraph agents, FastAPI, React, evaluation, testing and observability. Use when planning, implementing, reviewing, debugging or improving this project.
---

# Phishing AI Engineering Skill

## Primary objective

Build the AI Phishing Risk & Security Triage Platform as one coherent, realistic AI engineering system.

The project must prioritize:

- understanding over code volume
- evaluation over demo-only behavior
- simple architecture over unnecessary complexity
- incremental implementation over giant code generation
- real measurements over fabricated claims
- interview defensibility over technology count

The developer should be able to explain every core project component.

---

# Developer learning context

The developer is already comfortable with:

- JavaScript / TypeScript
- Node.js / Express
- React / Next.js
- PostgreSQL
- Redis
- Docker
- LangChain
- LangGraph
- RAG
- embeddings
- vector stores
- agents
- tool calling
- memory
- human-in-the-loop
- MCP
- hybrid search
- reranking
- knowledge graphs
- LangSmith
- AWS Bedrock
- LoRA / QLoRA concepts
- general LLM concepts

The developer is currently learning:

- Python for ML
- scikit-learn
- classical ML
- statistics for ML
- feature engineering
- evaluation metrics
- PyTorch
- Hugging Face NLP
- FastAPI
- ML/data pipelines

Therefore, introduce these concepts immediately before they are used.

Never assume deep prior knowledge of these areas.

---

# Teaching protocol

For every meaningful technical component explain:

## 1. Simple intuition

Explain the concept using normal language and the current phishing project.

## 2. Project flow

Show where the component sits in the system.

Example:

Input email
→ preprocessing
→ feature extraction
→ ML model
→ risk score

## 3. Technical explanation

Explain the engineering concept accurately.

## 4. Implementation

Implement only the required portion.

## 5. Code walkthrough

Explain important files, classes, functions and non-obvious lines.

Do not explain every obvious syntax token.

## 6. Verification

Provide commands/tests/checks and explain what successful output means.

## 7. Interview understanding

Explain:

- what it does
- why we use it
- alternatives
- tradeoffs
- limitations
- likely interview questions

---

# Two-level explanations

For difficult concepts, always provide:

### Level 1 — simple

Explain so a beginner can understand it.

### Level 2 — technical

Explain it at internship interview level.

Example:

Level 1:
Precision tells us how many predictions marked as phishing were actually phishing.

Level 2:
Precision = TP / (TP + FP), and it matters when false positives have meaningful operational cost.

---

# Architecture principles

Prefer:

- modular monolith
- clear service boundaries
- typed interfaces
- configuration through environment variables
- small testable functions
- explicit data flow
- clean dependency boundaries
- structured logging
- proper errors
- secure defaults

Avoid unnecessary:

- microservices
- Kubernetes
- Kafka
- Spark
- distributed systems
- multiple databases
- multiple agent frameworks
- complex infrastructure

unless a genuine requirement emerges.

---

# Development protocol

Never implement the whole project at once.

Work in small coherent phases.

Before each phase:

1. Explain the objective.
2. Explain why it is needed.
3. Explain where it fits.
4. State files that will change.
5. State what the developer will learn.

Then implement.

After implementation:

1. Run verification.
2. Report files changed.
3. Explain important decisions.
4. Explain failures if any.
5. Confirm tests/checks.
6. State the next logical phase.

Never silently jump across multiple major architectural phases.

---

# ML protocol

Start with a simple baseline before sophisticated models.

Explain:

- dataset
- target variable
- features
- train/validation/test
- preprocessing
- leakage
- imbalance
- baseline
- cross-validation
- overfitting
- metrics

Use real measured results.

Never invent accuracy, F1, AUC, latency or improvement numbers.

---

# NLP protocol

Start simple where useful.

Then introduce transformer-based NLP.

Explain:

- tokenization
- embeddings
- transformer input
- attention conceptually
- classification head
- fine-tuning
- epochs
- batches
- learning rate
- validation
- overfitting
- saving/loading models

Use an appropriately sized model.

Do not use a huge model merely for appearance.

---

# Evaluation protocol

Evaluation is a first-class project component.

Where applicable measure:

- accuracy
- precision
- recall
- F1
- ROC-AUC
- confusion matrix
- false positives
- false negatives
- retrieval quality
- groundedness
- hallucination
- latency
- cost
- agent/tool success and failure

Store or document the actual experiment results.

Never fabricate metrics.

---

# Agentic AI protocol

ML/NLP should generate measurable signals.

The LangGraph agent should primarily orchestrate:

- investigation
- retrieval
- tools
- evidence
- policy lookup
- explanation
- escalation

Do not make the LLM the only source of truth for risk classification if deterministic/model-based signals are available.

Use agents where they provide meaningful value.

---

# RAG protocol

Build basic RAG first:

documents
→ chunking
→ embeddings
→ vector retrieval
→ context
→ LLM

Only after baseline RAG works consider:

- hybrid search
- reranking
- retrieval evaluation

Explain why each improvement is needed.

---

# API protocol

Use FastAPI as the model/agent serving layer.

Keep API concerns separate from ML and agent logic.

Use:

- Pydantic schemas
- validation
- explicit error handling
- health checks
- configuration management
- API versioning where useful
- testable service functions

Do not bury model logic directly inside API routes.

---

# Security protocol

This is a defensive security project.

Do not interact with live malicious infrastructure merely for demonstration.

Prefer:

- public datasets
- static analysis
- safe URL parsing
- mock/sandboxed tools
- controlled test data

Never expose secrets.

Never hardcode API keys.

---

# Code quality protocol

Avoid:

- giant functions
- duplicate logic
- unexplained magic numbers
- unnecessary abstractions
- meaningless comments
- fake placeholder implementations presented as complete
- hardcoded environment-specific values

Use clear names and straightforward code.

Prefer boring, maintainable engineering.

---

# Testing protocol

Add tests as components are implemented.

Appropriate tests may include:

- unit tests
- preprocessing tests
- feature tests
- model inference tests
- API tests
- retrieval tests
- tool tests
- agent workflow tests

Do not leave all testing until the end.

---

# Git protocol

Use logical commits.

Examples:

feat: add phishing dataset preprocessing

feat: add baseline phishing classifier

feat: expose prediction service through FastAPI

feat: add LangGraph investigation workflow

test: add phishing feature validation tests

docs: document model evaluation

Do not make one giant commit containing the entire project.

---

# Resume protocol

The final resume must contain only claims supported by actual implementation.

Do not invent:

- users
- performance improvements
- model accuracy
- business impact
- latency gains
- cost savings

Choose only the strongest 3–4 technical outcomes.

Technology names should appear only when they materially represent work performed.

---

# Decision rule

Whenever two approaches are possible:

Choose the approach that is:

1. simpler
2. easier to verify
3. easier to explain
4. easier to maintain
5. still sufficient for the project goal

Only choose the more complex alternative when there is a clear technical reason.

---

# End-of-phase checkpoint

At the end of each major phase provide:

### What we built

### Why we built it

### How it works

### What changed

### How we verified it

### What I should remember

### Interview questions I should now be able to answer

### Next phase

Do not continue to the next major phase until the current phase is verified.

# Continuous Learning Notes

This is a learning-first project.

Maintain `docs/learning/` throughout development.

Whenever the developer asks a meaningful question, expresses confusion about a reusable technical concept, learns a new technology, encounters a debugging issue, or makes an important engineering decision:

- identify the reusable lesson
- explain it clearly
- update the appropriate learning document
- keep the documentation synchronized with the real implementation

Do this proactively. The developer should not need to repeatedly ask for documentation updates.

Do not dump raw conversation transcripts into markdown files.

Convert discussions into clean, reusable educational notes.

Important doubts should be preserved conceptually, for example:

Question:
"Why do we use recall instead of only accuracy for phishing detection?"

Learning:
Explain the concept, show the phishing-specific example, give the formula, explain the tradeoff, and record the interview takeaway.

When a concept is revisited later, update the existing note instead of creating duplicate documentation.

At the end of each major phase, verify that the relevant learning notes were updated.

At project completion, create a consolidated interview revision document based only on concepts actually used or learned during this project.