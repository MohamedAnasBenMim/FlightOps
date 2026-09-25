# FlightOps

FlightOps is a weather-aware drone mission planning backend. It will evaluate
planned drone missions against aircraft operational limits and forecast weather
conditions.

> FlightOps is a technical decision-support prototype and portfolio project. It
> is not a certified aviation safety system and must not be used as the sole
> basis for real-world flight decisions.

## Current status

The project is in its initial foundation phase. It currently provides:

- A minimal FastAPI application.
- A `GET /health` endpoint.
- Automated formatting, linting, type checking, and tests.

Aircraft, missions, weather integration, risk assessment, persistence, and
flight-window recommendations have not been implemented yet.

## Requirements

- Python 3.12
- Git

## Local setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project and development dependencies:

```bash
python -m pip install --editable ".[dev]"
```

## Run the API

Start the local development server:

```bash
uvicorn flightops.main:app --reload --host 127.0.0.1 --port 8000
```

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

If port `8000` is already in use, select another port:

```bash
uvicorn flightops.main:app --reload --host 127.0.0.1 --port 8001
```

Remember to use the same port when calling the health endpoint.

## Quality checks

Automatically format the code:

```bash
ruff format .
```

Run linting:

```bash
ruff check .
```

Run static type checking:

```bash
mypy
```

Run the tests:

```bash
pytest
```

Confirm that no formatting changes are needed:

```bash
ruff format --check .
```

Run these checks after each small implementation step and before committing.

## Project documentation

- [`PROJECT.md`](PROJECT.md) defines the problem, scope, architecture principles,
  and domain concepts.
- [`ROADMAP.md`](ROADMAP.md) tracks the planned development phases and completed
  steps.
- [`AGENTS.md`](AGENTS.md) defines the mentoring and contribution workflow.