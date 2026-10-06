# AI Phishing Risk & Security Triage Platform

A learning-first AI engineering project that combines classical ML, NLP, and agentic workflows to analyze and triage suspicious emails.

## Setup

This project uses Python 3.11+.

```bash
# 1. Activate the virtual environment
source env/bin/activate

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

See [docs/architecture.md](docs/architecture.md) for full details.
