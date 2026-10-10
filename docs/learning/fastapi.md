# FastAPI — Learning Notes

*Maintained throughout Phase 6. Updated incrementally as each sub-step is implemented.*

---

## Table of Contents

1. [What is ASGI and why FastAPI uses it](#1-what-is-asgi-and-why-fastapi-uses-it)
2. [Application factory and `create_app()`](#2-application-factory-and-create_app)
3. [Routing with APIRouter](#3-routing-with-apirouter)
4. [Lifespan — the modern startup/shutdown hook](#4-lifespan--the-modern-startupshutdown-hook)
5. [Pydantic v2 schemas for request and response](#5-pydantic-v2-schemas-for-request-and-response)
6. [Testing FastAPI with TestClient](#6-testing-fastapi-with-testclient)
7. [Concepts to be added in later sub-steps](#7-coming-in-later-sub-steps)

---

## 1. What is ASGI and why FastAPI uses it

### Level 1 — simple

**WSGI** (older Python standard) passes one HTTP request to your app, waits for the full response, then moves on.  It's fine for normal web pages, but it can't handle long-lived connections (WebSockets) or real concurrency without multiple OS threads.

**ASGI** (Asynchronous Server Gateway Interface) lets your Python code say "I'm waiting for the database — handle another request in the meantime."  This is `async/await` in practice.

### Level 2 — technical

ASGI is a spec (PEP-like document) that defines a three-part calling convention between an ASGI server (Uvicorn, Hypercorn) and an ASGI app (FastAPI, Starlette):

```
scope  — dict describing the connection (type, path, headers…)
receive — async callable to read the next event from the client
send   — async callable to send events back
```

FastAPI is built on **Starlette** which implements the ASGI interface.  Uvicorn is the process that accepts TCP connections and speaks the ASGI protocol to FastAPI.

**Why this matters for the phishing platform:**
In later sub-steps we'll do async PostgreSQL writes (`asyncpg` driver).  ASGI means the event loop is not blocked while waiting for the DB — the same worker can process another `/analyze` call concurrently.

### In this project

```
Client HTTP request
    → Uvicorn (ASGI server)
    → FastAPI (ASGI application / Starlette core)
    → our route handler
    → Pydantic validation
    → ML inference (sync, wrapped)
    → PostgreSQL write (async in sub-step G)
    → response
```

---

## 2. Application factory and `create_app()`

### What it is

`create_app()` is a function that builds and returns a configured `FastAPI()` instance.  It lives in `src/api/app.py`.

### Why a factory instead of a module-level global

**Direct module-level:**
```python
# src/api/app.py  — anti-pattern for testability
app = FastAPI()          # created at import time
```

**Factory function:**
```python
def create_app() -> FastAPI:
    app = FastAPI(...)    # created when called
    ...
    return app
```

The factory is better because:
- Each test can call `create_app()` independently → no shared mutable state between tests.
- We can pass in settings or override dependencies per test.
- The production entry-point (`uvicorn src.api.app:app`) just calls the factory once.

### Production entry-point

We'll add a small `main.py` shim later:
```python
# src/main.py (not yet created)
app = create_app()   # uvicorn src.main:app
```

---

## 3. Routing with APIRouter

### What it is

`APIRouter` is FastAPI's way of grouping related routes into a module without coupling them to the app instance.

### Pattern used in this project

```python
# src/api/routes/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse: ...
```

```python
# src/api/app.py
from src.api.routes.health import router as health_router
app.include_router(health_router, tags=["Health"])
```

### Why not put routes directly on `app`?

If all routes were on `app`, the entire route list would be in `app.py`.  As the API grows (`/health`, `/analyze`, future `/explain`, `/agent`) it becomes one large file.  `APIRouter` lets us split routes by feature while the app stays a thin coordinator.

### URL prefix

In later sub-steps the analyze router will be mounted with:
```python
app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
```
This gives us clean versioning (`/api/v1/analyze`) without repeating `/api/v1` in every route decorator.

---

## 4. Lifespan — the modern startup/shutdown hook

### What it is

`lifespan` is a single `async` context manager that runs startup code *before* the app accepts requests, and shutdown code *after* the last request is processed.

### Old approach (deprecated in FastAPI 0.93)

```python
@app.on_event("startup")       # deprecated
async def load_models(): ...

@app.on_event("shutdown")      # deprecated
async def unload_models(): ...
```

### New approach (used in this project)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("application_startup")
    # load ML models, create DB pool, etc.
    yield                         # ← app serves requests here
    # --- SHUTDOWN ---
    logger.info("application_shutdown")
    # release resources

app = FastAPI(..., lifespan=lifespan)
```

**Why it's better:**
- Startup and shutdown are one coherent block — if startup fails, the shutdown code in the same `try/finally` pattern still runs.
- It's the standard Python context manager pattern — easier to test and reason about.
- FastAPI's own docs and examples now use this pattern.

### What lifespan will do in sub-step F (model loading)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load classical ML model once at startup
    app.state.classical_model = load_model()
    # Load DistilBERT tokenizer + model once at startup
    app.state.nlp_model = load_nlp_model()
    yield
    # Nothing to release for in-process models
```

`app.state` is a simple namespace FastAPI provides for storing app-level objects that route handlers can access via `request.app.state`.

---

## 5. Pydantic v2 schemas for request and response

### What Pydantic does

Pydantic reads a type-annotated class and gives you:
1. **Automatic parsing** — `AnalyzeRequest(**json_body)` converts strings to typed values.
2. **Automatic validation** — if `text=""` is passed, Pydantic raises `ValidationError` before your code runs.
3. **Serialisation** — `.model_dump()` converts the model back to a dict for JSON output.

### How FastAPI connects Pydantic to HTTP

```python
@router.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    ...
```

- `request: AnalyzeRequest` — FastAPI reads the JSON body, passes it to `AnalyzeRequest(**body)`, and returns 422 automatically if validation fails.
- `response_model=AnalyzeResponse` — FastAPI runs the return value through `AnalyzeResponse` before serialising it to JSON.  This prevents accidentally leaking extra internal fields.

### Schemas defined in this project

| Schema | Purpose |
|---|---|
| `HealthResponse` | GET /health body |
| `AnalyzeRequest` | POST /api/v1/analyze body |
| `AnalyzeResponse` | POST /api/v1/analyze response |
| `ErrorResponse` | 4xx/5xx error bodies |

### Field constraints example

```python
risk_score: float = Field(..., ge=0.0, le=100.0)
```
`ge=0.0` means "greater than or equal to 0.0".  If `risk_score=-1` is returned, Pydantic raises `ValidationError` before the response is sent.  This is the same validation on output as on input.

### Custom validator example (whitespace-only text)

```python
@field_validator("text")
@classmethod
def text_must_not_be_whitespace_only(cls, value: str) -> str:
    if not value.strip():
        raise ValueError("text must contain at least one non-whitespace character")
    return value
```

`field_validator` in Pydantic v2 replaces `@validator` from v1.  It runs after the built-in type check (so `value` is already a `str`) and before the value is stored on the model.

### Interview question: why define response schemas separately from request schemas?

- **Request schemas** define what the *client* must provide.
- **Response schemas** define what *we guarantee to the client*.
- They often share fields but have different validation rules:
  - `request_id` is *generated by the server* (not in the request schema).
  - `analysis_id` may be `None` before DB is wired up (nullable in response).
- Separate schemas prevent coupling: changing the DB model doesn't force a change to the API contract.

---

## 6. Testing FastAPI with TestClient

### What TestClient is

`TestClient` (from `starlette.testclient`) is an `httpx` client that talks to your ASGI app *in the same process* — no TCP socket, no network.

This means:
- Tests run fast (no port binding, no OS network stack).
- Tests are reproducible (no "port already in use" errors).
- Tests can inject dependencies, mock services, etc.

### Pattern used in this project

```python
# tests/test_api/conftest.py
from fastapi.testclient import TestClient
from src.api.app import create_app

@pytest.fixture(scope="session")
def client():
    with TestClient(create_app()) as c:
        yield c
```

**Key: `with TestClient(app) as c`**

The `with` block fires `lifespan` startup before yielding `c` and fires shutdown after the test session ends.  Without the `with`, lifespan events are NOT triggered — startup code (model loading in sub-step F) would never run.

### Why `scope="session"`?

Creating a FastAPI app and firing lifespan has cost (model loading in sub-step F will be expensive).  `scope="session"` means pytest creates the client once and shares it across all tests.

This is safe as long as tests don't mutate app-level state.  Stateful tests (e.g. DB-writing tests in sub-step G) should each use a transaction rollback fixture or an isolated test database.

### Example test pattern

```python
def test_returns_200(self, client):
    response = client.get("/health")
    assert response.status_code == 200
```

`client` here is the pytest fixture from `conftest.py`.  pytest injects it automatically based on the argument name.

---

## 7. Coming in later sub-steps

| Sub-step | Topic |
|---|---|
| F | Request ID middleware, structlog JSON logging |
| F | ML model loading in lifespan |
| F | POST /api/v1/analyze implementation |
| G | SQLAlchemy + PostgreSQL — engine, session, models |
| G | Repository pattern for DB persistence |
| H | Full exception handlers (422, 500, custom) |
| I | Complete API test suite with mocked models |

---

*This document will be updated as each sub-step is implemented. The examples above are always from the actual project code, not textbook examples.*
