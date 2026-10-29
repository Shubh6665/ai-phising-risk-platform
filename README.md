# AI Phishing Risk & Security Triage Platform

A learning-first AI engineering project that combines classical ML, NLP, and agentic workflows to analyze and triage suspicious emails.

## Setup

### 1. Backend (FastAPI + ML/NLP + RAG + LangGraph)

This project supports Python 3.11 to 3.13 (`>=3.11,<3.14`) and is developed on Python 3.12.

```bash
# 1. Create and activate the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (editable mode)
pip install -e ".[dev,data,agent]"

# 3. Configure environment
cp .env.example .env
# Edit .env with your keys (HF_TOKEN, DATABASE_URL, GOOGLE_API_KEY, GROQ_API_KEY)

# 4. Start the backend API server
uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Dashboard (React + Vite + Tailwind + Recharts)

Requires Node.js 18+ (tested on Node 22.13.1).

```bash
# 1. Navigate to frontend directory and install dependencies
cd frontend
npm install

# 2. Configure environment (optional, defaults to http://localhost:8000)
cp .env.example .env.local

# 3. Start local development server
npm run dev

# 4. Run frontend unit tests and type checks
npm test
npm run typecheck

# 5. Build for production
npm run build
```

## Running Backend Tests

```bash
# Run full offline test suite
pytest tests/ -v
```

## Architecture

See [docs/learning/architecture.md](docs/learning/architecture.md) for full details.
