# FlightOps — Project Definition

## Status

Draft for review. This document defines the intended MVP; it is not a claim that
the listed capabilities have already been implemented.

## Problem

Planning a drone mission requires comparing an aircraft's operational limits
with weather conditions across a route and over time. Doing this manually is
slow, inconsistent, and easy to oversimplify: weather can differ between
waypoints, the most limiting condition may occur on only one route segment, and
a mission that is unsuitable now may become suitable at a later departure time.

FlightOps addresses the software-engineering problem of producing a repeatable,
explainable operational assessment from aircraft constraints, route geometry,
and forecast weather.

FlightOps is a technical decision-support prototype and educational portfolio
project. It is not a certified aviation safety system, does not replace a pilot
or operator's judgment, and must not be used as the sole basis for a real-world
flight decision.

## Proposed solution

Build a cloud-ready REST API that:

1. Stores aircraft and their configured operational limits.
2. Stores missions made of ordered geographic waypoints.
3. Retrieves forecast weather for relevant route locations and times.
4. Converts provider-specific responses into an internal weather model.
5. Evaluates route segments with deterministic, explicit rules.
6. Aggregates segment results into a mission status of `SAFE`, `WARNING`, or
   `UNSAFE`.
7. Reports the main limiting factor and supporting details.
8. Evaluates candidate departure times and recommends suitable flight windows.
9. Persists the inputs and results so an assessment can be inspected later.

The first version will be a modular monolith: one deployable FastAPI application
with clear internal boundaries between API, application/domain logic,
persistence, and external integrations.

## Target users and use cases

### Primary target user

A drone operator or mission planner who wants a consistent preliminary weather
feasibility assessment before a planned mission.

### Secondary target users

- A fleet or operations manager reviewing why a mission was accepted or
  rejected.
- A developer integrating mission assessment into another operational tool.
- A technical interviewer evaluating the architecture and engineering decisions
  demonstrated by the project.

### Core use cases

- Register an aircraft with limits such as maximum wind, gust, precipitation,
  and allowed temperature range.
- Create a mission with an aircraft, planned departure time, and ordered
  waypoints.
- Request an assessment for that mission.
- Inspect the status and reasons for each route segment and the whole mission.
- Identify the condition with the smallest safety margin or a breached limit.
- Compare candidate departure times.
- Retrieve recommended flight windows.
- Retrieve a stored mission, weather snapshot, and assessment for audit and
  explanation.

## Project scope

The project covers the backend path from validated API input through persistence,
weather integration, deterministic analysis, testing, containerized local
development, CI, and cloud deployment.

The MVP includes:

- Aircraft creation and retrieval with validated operational constraints.
- Mission creation and retrieval with at least two ordered WGS84 latitude and
  longitude waypoints and a timezone-aware planned departure time.
- Route segmentation between consecutive waypoints.
- Forecast retrieval from Open-Meteo for the route and relevant times.
- Translation of Open-Meteo data into a provider-independent internal model.
- Immutable weather snapshots associated with an assessment.
- Explicit rules for wind, gusts, precipitation, temperature, and forecast
  availability.
- Segment-level results and an overall `SAFE`, `WARNING`, or `UNSAFE` result.
- An explanation of breached or near-limit constraints and the principal
  limiting factor.
- Evaluation of departure candidates within a defined search period and
  recommendation of contiguous suitable windows.
- PostgreSQL persistence through SQLAlchemy and Alembic migrations.
- A documented FastAPI REST interface and consistent error responses.
- Unit tests for domain rules and focused integration tests for persistence,
  provider adaptation, and API behavior.
- Local execution using Docker Compose.
- GitHub Actions checks for tests and code quality.
- Deployment as one containerized API on AWS ECS Fargate, using Amazon ECR,
  Amazon RDS for PostgreSQL, and CloudWatch for logs.

## MVP boundary and success criteria

The MVP is successful when a reviewer can run the system locally, create an
aircraft and mission, obtain and later retrieve an explainable assessment based
on persisted forecast data, request recommended departure windows, and see the
same deterministic inputs produce the same result. Automated tests and CI must
cover the important rules, and the API must be deployable to the selected AWS
architecture.

Numerical warning thresholds and aggregation rules will be chosen and documented
when the risk-engine phase begins. They will not be implied to represent legal or
certified aviation standards.

## Non-goals for the MVP

- Certified flight authorization, regulatory compliance, or a safety guarantee.
- Live vehicle control, telemetry ingestion, autopilot integration, or route
  execution.
- Authentication, authorization, user accounts, or multi-tenancy.
- A web or mobile frontend.
- AI, machine learning, probabilistic risk scoring, or LLM-generated decisions.
- Microservices, event-driven infrastructure, or background job orchestration.
- No-fly-zone or restricted-airspace analysis.
- Terrain, obstacle, battery-consumption, payload, radio-link, or traffic
  analysis.
- PostGIS or advanced geospatial queries.
- Multiple weather providers or provider consensus.
- Historical analytics and long-term forecast verification.
- High availability, multi-region disaster recovery, or internet-scale load.

## Architecture principles

- **Modular monolith first:** keep one application and deployment unit while
  maintaining clear module boundaries.
- **Dependency direction:** domain rules must not depend on FastAPI, SQLAlchemy,
  PostgreSQL, or Open-Meteo response shapes.
- **Separation of concerns:** HTTP handling, use-case orchestration, domain
  decisions, persistence, and external integrations have distinct
  responsibilities.
- **Explicit domain models:** represent operational concepts and invariants with
  typed, meaningful models rather than unstructured dictionaries.
- **Deterministic and explainable decisions:** the same normalized input and rule
  version must produce the same status and reasons.
- **Provider isolation:** access Open-Meteo through a small interface and adapter
  so domain logic consumes only the internal weather representation.
- **Persistence isolation:** keep database mapping concerns out of core decision
  rules; introduce repository boundaries only where they solve a concrete need.
- **Dependency injection at boundaries:** inject database sessions, weather
  clients, and clocks where doing so makes behavior controllable and testable.
- **Validation at the edge and invariants in the core:** reject malformed API
  data early while preserving rules that must always hold in domain code.
- **UTC internally:** accept timezone-aware timestamps, normalize stored and
  compared instants to UTC, and make time-window semantics explicit.
- **Small, reversible increments:** introduce abstractions and dependencies only
  when a current feature requires them.
- **Operational visibility:** use structured logs, health endpoints, and useful
  error handling without logging secrets or sensitive configuration.
- **Reproducibility:** pin dependencies, version database changes, and keep local
  and CI workflows aligned.

## High-level architecture

The modular monolith will have four conceptual areas:

- **API layer:** FastAPI routes, request/response schemas, HTTP status codes, and
  exception translation.
- **Application and domain layer:** use-case orchestration, domain models,
  operational-limit evaluation, result aggregation, and flight-window logic.
- **Persistence layer:** SQLAlchemy models, repositories or query functions,
  transactions, and Alembic migrations for PostgreSQL.
- **Integration layer:** the Open-Meteo client and translation into the internal
  weather model.

The exact package structure will be selected when the Python project is
initialized; this document intentionally describes responsibilities before
committing to folders.

## Technical stack

| Area | Technology | Reason for the MVP |
| --- | --- | --- |
| Language | Python | Strong ecosystem for APIs, validation, testing, and data transformation. |
| HTTP API | FastAPI | Typed REST endpoints, dependency injection, and generated OpenAPI documentation. |
| Validation | Pydantic | Boundary validation and serialization integrated with FastAPI. |
| ORM | SQLAlchemy | Explicit relational mapping, sessions, transactions, and mature PostgreSQL support. |
| Schema migrations | Alembic | Versioned and repeatable database schema evolution. |
| Database | PostgreSQL | Production-grade relational storage for missions, ordered waypoints, snapshots, and results. |
| Weather provider | Open-Meteo | Forecast API suitable for an initial provider adapter. |
| Tests | pytest | Readable unit and integration tests with fixtures and parametrization. |
| Packaging and runtime | Docker | Reproducible application runtime across development, CI, and AWS. |
| Local environment | Docker Compose | Coordinates the API and PostgreSQL for local development and integration tests. |
| CI | GitHub Actions | Automated quality and test checks for every change. |
| Container registry | Amazon ECR | Stores the deployable API image for ECS. |
| Compute | Amazon ECS on Fargate | Runs the container without managing EC2 hosts. |
| Managed database | Amazon RDS for PostgreSQL | Managed production PostgreSQL with backups and operational tooling. |
| Observability | Amazon CloudWatch | Centralized container logs and basic operational monitoring. |

Concrete versions, the HTTP client, database driver, formatter, linter, and type
checker will be selected only when introduced, with each choice documented.

## Key domain concepts

- **Aircraft:** the drone being evaluated, identified independently of any one
  mission.
- **Operational limits:** configured measurable boundaries for an aircraft, such
  as maximum sustained wind, maximum gust, precipitation tolerance, and minimum
  and maximum temperature.
- **Mission:** a planned flight using one aircraft, an ordered route, and a
  proposed departure time.
- **Waypoint:** an ordered geographic coordinate in WGS84 latitude/longitude.
- **Route segment:** the leg between two consecutive waypoints and the basic unit
  of route-level evaluation.
- **Candidate departure:** one possible mission start time considered during
  assessment or flight-window search.
- **Weather observation point:** normalized forecast conditions associated with
  a location and forecast time. Despite the name, this is forecast data, not a
  measured observation.
- **Weather snapshot:** the persisted, immutable normalized forecast input used
  for one assessment, with provider and retrieval metadata.
- **Constraint result:** the comparison of one weather metric with one aircraft
  limit, including its outcome, measured value, threshold, and explanation.
- **Segment assessment:** the constraint results and resulting status for one
  route segment.
- **Mission assessment:** the stored aggregate status, limiting factor, reasons,
  and metadata for one mission at one candidate departure time.
- **Assessment status:** an ordered domain outcome: `SAFE`, `WARNING`, or
  `UNSAFE`.
- **Limiting factor:** the breached constraint or smallest remaining operational
  margin that most strongly determines the result.
- **Flight window:** a contiguous interval of candidate departure times that
  meets the defined suitability rule.
- **Rule version:** an identifier for the deterministic policy used, allowing a
  stored result to remain explainable when rules later evolve.

Terms such as interpolation method, sampling interval, warning margin, missing
forecast behavior, and segment timing remain explicit design decisions for their
respective implementation phases.

## Major engineering challenges

- **Route-to-weather alignment:** deciding where and when weather is sampled for
  each segment without claiming false spatial or temporal precision.
- **External data normalization:** mapping provider units, nullable values,
  timestamps, and error modes into a stable internal contract.
- **Time handling:** consistently using timezone-aware datetimes and aligning
  candidate departures with available forecast intervals.
- **Explainable aggregation:** defining how individual constraint outcomes and
  segment statuses produce one mission status and one limiting factor.
- **Missing or stale forecasts:** failing safely and transparently when the
  provider cannot supply sufficient data.
- **Reproducibility:** persisting the actual normalized forecast inputs and rule
  version instead of silently recalculating history from changed forecasts.
- **Relational modeling:** preserving waypoint order and assessment relationships
  while keeping migrations safe and queries understandable.
- **Testing boundaries:** testing domain rules without network or database I/O,
  while still verifying the database, API, and provider adapter together where
  appropriate.
- **External-service resilience:** using timeouts, bounded retries where safe,
  clear errors, and test doubles without hiding provider failures.
- **Cloud operations and cost:** handling configuration, secrets, migrations,
  networking, logging, health checks, and least-privilege AWS access at portfolio
  scale.

## Possible future extensions

Only after the core MVP is complete and understood:

- PostGIS-backed geospatial storage and querying.
- AWS CDK infrastructure as code.
- A React and TypeScript route-planning interface.
- Map-based route and assessment visualization.
- Redis caching for carefully measured provider or query bottlenecks.
- Background jobs for long-running or scheduled reassessments.
- Restricted and no-fly-zone checks using authoritative data sources.
- Historical operational and forecast-accuracy analytics.
- Additional weather providers and comparison strategies.
- Battery, payload, terrain, obstacle, or communications-risk models.
- Authentication, authorization, organizations, and audit trails.

Each extension requires a concrete problem, an explicit design decision, and
tests; none should be introduced merely to expand the technology list.
