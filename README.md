# FlightOps

FlightOps is a weather-aware drone mission planning platform. It evaluates
forecast conditions along an ordered route against a selected aircraft's
operational envelope, explains every constraint result, preserves the normalized
forecast used for the decision, and recommends suitable departure windows.

> **Safety boundary:** FlightOps is a technical decision-support prototype and
> portfolio project. It is not a certified aviation safety system and must not
> be used as the sole basis for a real-world flight decision.

## What is implemented

- Vue 3 + TypeScript mission-control dashboard.
- Aircraft creation with validated wind, gust, rain, and temperature limits.
- Missions with ordered WGS84 waypoints and timezone-aware departures.
- Open-Meteo integration behind a provider-independent interface.
- Deterministic route-level SAFE, WARNING, and UNSAFE rules.
- Explainable segment constraints and a stable limiting factor.
- Immutable normalized weather snapshots and versioned persisted assessments.
- Bounded alternative-departure evaluation and contiguous flight windows.
- FastAPI OpenAPI documentation and consistent API errors.
- PostgreSQL, SQLAlchemy, and an Alembic migration.
- Unit, API, provider-normalization, and PostgreSQL integration tests.
- Non-root production containers, Docker Compose, and GitHub Actions CI.
- Structured request logs plus separate liveness and readiness endpoints.

AWS deployment automation is ready, but live provisioning requires valid AWS credentials and explicit cost acceptance.

## Architecture

FlightOps is a modular monolith. HTTP concerns, use-case orchestration, pure
domain rules, persistence, and the weather adapter are separate while remaining
one deployable API. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the
boundaries and engineering decisions.

~~~text
Vue client → FastAPI routes → application services → domain/risk rules
                         ↘ SQLAlchemy/PostgreSQL
                         ↘ Open-Meteo adapter
~~~

## Run the complete stack

Requirements: Docker with Compose.

~~~bash
cp .env.example .env
docker compose build
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d
~~~

Open:

- Dashboard: <http://localhost:18080>
- API documentation: <http://localhost:18000/docs>
- Liveness: <http://localhost:18000/health/live>
- Readiness: <http://localhost:18000/health/ready>

Inspect status and logs:

~~~bash
docker compose ps
docker compose logs -f api
~~~

Stop services with docker compose down. To intentionally delete local database
data, add the --volumes option.

## Backend development

Requirements: Python 3.12 and a PostgreSQL 17 instance for integration tests.

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn flightops.main:app --reload
~~~

The application defaults to a local SQLite file only as a convenient
zero-configuration development fallback. Docker Compose, CI, and the intended
runtime use PostgreSQL.

Quality and tests:

~~~bash
ruff format --check .
ruff check .
mypy
pytest -q
~~~

Run the PostgreSQL integration test by setting TEST_DATABASE_URL to a dedicated
migrated test database. Never point it at production.

## Frontend development

Requirements: Node.js 20.

~~~bash
cd frontend
npm ci
npm run dev
~~~

Vite proxies /api and /health to <http://localhost:8000>. To call another API
origin, set VITE_API_BASE_URL before building.

~~~bash
npm test
npm run typecheck
npm run build
npm audit
~~~

## Database migrations

After changing SQLAlchemy mappings, create and review a migration, then run
alembic upgrade head. Production migrations should run as an explicit one-off
task before a new service version receives traffic. They are intentionally not
run concurrently by every API container.

## API workflow

The main sequence is:

1. POST /api/v1/aircraft
2. POST /api/v1/missions
3. POST /api/v1/missions/{mission_id}/assessments
4. GET /api/v1/assessments/{assessment_id}
5. GET /api/v1/missions/{mission_id}/flight-windows

Examples and response semantics are in [docs/API.md](docs/API.md).

## Rule semantics

Rule version 2026-01 uses these deterministic policies:

- A missing required forecast value fails closed as UNSAFE.
- A value above a configured maximum is UNSAFE.
- A value at or above 80% of a maximum is WARNING.
- Temperature outside its inclusive configured range is UNSAFE.
- Temperature within 20% of either end of its configured range is WARNING.
- Segment and mission aggregation use worst-severity precedence.
- The limiting factor is the worst-severity constraint with the smallest
  numeric margin, then metric name as a stable tie-break.

These are transparent prototype rules, not regulatory or manufacturer guidance.

## AWS deployment

Review docs/DEPLOYMENT.md before provisioning. The expected us-east-1 portfolio cost is approximately $48–65 per month before tax and unusual traffic. The deployment script requires valid AWS credentials, a clean Git worktree, and CONFIRM_AWS_COSTS=YES. Infrastructure templates are validated in CI; no live AWS resources have been created from this repository yet.

## Documentation

- [PROJECT.md](PROJECT.md) — product boundary and success criteria
- [ROADMAP.md](ROADMAP.md) — implementation progress and next deployment phase
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — component and data-flow design
- [docs/API.md](docs/API.md) — API examples and errors
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — AWS design, costs, deployment, rollback, and teardown
- [docs/SECURITY.md](docs/SECURITY.md) — implemented controls and accepted MVP risks
- [docs/DEMO.md](docs/DEMO.md) — reproducible portfolio demonstration
- [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md) — architecture and tradeoff explanations
- [docs/PORTFOLIO_AUDIT.md](docs/PORTFOLIO_AUDIT.md) — claim-by-claim completion audit
- [AGENTS.md](AGENTS.md) — contribution and learning workflow
