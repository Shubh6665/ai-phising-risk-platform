# Architecture

## Simple Explanation

We are building a single Python application (a "modular monolith") that takes in an email, extracts features from it, passes them to AI models to get a risk score, and then uses a LangGraph agent to explain why it's risky and recommend what to do.

## Why We Need It

Separating the deterministic ML models from the agentic reasoning makes the system reliable and testable. The ML models give us measurable, hard numbers. The agent gives us human-readable context. 

## Project Flow

User Input (Email + URL)
↓
FastAPI Backend
↓
Feature Extraction (text features + URL features from the same email)
↓
Classical ML Model + NLP Transformer Model
↓
Ensemble (calculates final risk score 0-100)
↓
LangGraph Agent (retrieves policies, reasons over evidence)
↓
PostgreSQL (saves result)
↓
React UI (shows result to user)

## Technical Explanation

### Modular Monolith
All backend code runs in one single Python process. We use Python packages (directories with `__init__.py`) to enforce boundaries instead of microservices. This is the correct pattern for a single-developer AI project because it eliminates network latency between components, simplifies deployment, and makes testing much easier, while still teaching separation of concerns.

### Typed Configuration
In our configuration (`src/config.py`), we use `pydantic-settings`. It reads environment variables and the local `.env` file and validates their types when `Settings()` is created, so a wrongly typed value fails immediately.

The API keys (`GOOGLE_API_KEY`, `GROQ_API_KEY`) and `DATABASE_URL` are deliberately `Optional` with a default of `None`, so a missing key does **not** crash the app at startup. This lets us run tests and the ML phases without any LLM keys. The check that a key is present happens later, when the LLM client is actually initialized (Phase 8).

(Dependency injection is a separate concept, planned for FastAPI in Phase 6.)

### Python Version
The project targets Python 3.11 to 3.13 and is developed on Python 3.12, with the virtual environment in `.venv/`. Phase 1 was initially built on the macOS system Python 3.9, which is end-of-life and too old for recent releases of libraries planned for later phases, so the environment was recreated on 3.12.

## Important Decisions

1. **No Microservices**: We deliberately avoided Kubernetes, Kafka, and multiple services. They add operational complexity that distracts from the core AI engineering goals.
2. **Kaggle for Training**: NLP models (Transformers) will be trained remotely on Kaggle GPUs to avoid local hardware bottlenecks, but the *source code* remains in this repository to act as the single source of truth.
3. **LLM Provider Agnostic**: The agent is designed to use Gemini 3.8 Flash (via Google AI Studio free tier) as the primary provider, with Groq as a fallback, controlled purely via configuration (`src/config.py`), not by writing provider-specific product features.

## Interview Perspective

**"Why did you choose a monolithic architecture instead of microservices?"**
*"For this project, the primary complexity was in the data pipelines, model integration, and agent orchestration. A modular monolith enforced clean separation of concerns through Python package boundaries without the operational overhead of microservices. It allowed me to focus on building robust ML and RAG pipelines rather than debugging network boundaries, while keeping the architecture easily deployable and testable."*
