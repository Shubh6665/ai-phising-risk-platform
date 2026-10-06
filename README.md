# AI Phishing Risk & Security Triage Platform

A learning-first AI engineering project that combines classical ML, NLP, and agentic workflows to analyze and triage suspicious emails.

## Setup

This project supports Python 3.11 to 3.13 (`>=3.11,<3.14`) and is developed on Python 3.12.

```bash
# 1. Create and activate the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (editable mode)
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env
# Edit .env with your keys
```

## Running Tests

```bash
pytest tests/ -v
```

## Architecture

See [docs/learning/architecture.md](docs/learning/architecture.md) for full details.
