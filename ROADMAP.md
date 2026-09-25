# FlightOps — Development Roadmap

## How to use this roadmap

This is a learning roadmap, not a delivery race. We complete one small numbered
step at a time. For every implementation step, the mentor first explains the
goal, reason, concept, files, task, hints, verification, expected result, and
interview takeaway. The student implements it, then the mentor reviews it before
the next step begins.

A checkbox may be marked complete only when:

- the planned implementation or document exists;
- the relevant checks pass (or the step is documentation-only);
- the student can explain the important decision and tradeoff.

Status: **approved; Phase 1 is ready to begin**.

## Phase 0 — Agree on the project plan

- [x] **Step 0.1 — Review and approve the project definition.** Confirm the
  problem, users, MVP boundary, non-goals, architecture principles, and domain
  vocabulary in `PROJECT.md`.
- [x] **Step 0.2 — Review and approve the delivery sequence.** Adjust this
  roadmap so its increments match the desired learning pace and portfolio goal.

**Phase outcome:** project scope and sequence are understood and explicitly
agreed before application work starts.

## Phase 1 — Establish the development foundation

- [x] **Step 1.1 — Initialize version control and repository hygiene.** Verify or
  initialize Git, choose the initial branch convention, and add a Python-focused
  `.gitignore` without adding application code.
- [ ] **Step 1.2 — Create the minimal Python project configuration.** Choose a
  supported Python version and dependency-management approach; add project
  metadata and an importable package skeleton.
- [ ] **Step 1.3 — Add development quality tools.** Configure formatting,
  linting, and static type checking with the smallest useful rule set.
- [ ] **Step 1.4 — Add the first pytest smoke test.** Establish test discovery and
  a repeatable local quality command.
- [ ] **Step 1.5 — Create the minimal FastAPI application.** Add an app factory or
  application entry point and a simple health endpoint.
- [ ] **Step 1.6 — Test the health endpoint.** Use FastAPI's test client to verify
  the first API contract without starting a real server.
- [ ] **Step 1.7 — Document the local developer workflow.** Record setup, run,
  quality, and test commands in `README.md`.

**Phase outcome:** a typed, testable minimal API can be run locally with a clear
developer workflow.

## Phase 2 — Model and test aircraft operational limits

- [ ] **Step 2.1 — Define aircraft and operational-limit vocabulary.** Decide the
  initial fields, units, inclusivity of boundaries, and required invariants.
- [ ] **Step 2.2 — Implement the aircraft domain model.** Represent the agreed
  concepts independently of HTTP and database concerns.
- [ ] **Step 2.3 — Unit-test aircraft invariants.** Cover valid boundaries and
  invalid combinations with focused tests.
- [ ] **Step 2.4 — Define aircraft API schemas.** Add request and response models
  with clear validation and examples.
- [ ] **Step 2.5 — Add an in-memory aircraft use case.** Implement create and get
  behavior behind a small persistence boundary before introducing PostgreSQL.
- [ ] **Step 2.6 — Expose aircraft endpoints.** Add create and retrieve routes
  with explicit status codes and error behavior.
- [ ] **Step 2.7 — Add aircraft API tests.** Verify success, validation failure,
  duplicate handling, and not-found behavior.

**Phase outcome:** the aircraft contract and its operational constraints work
end to end without coupling domain rules to infrastructure.

## Phase 3 — Introduce PostgreSQL persistence

- [ ] **Step 3.1 — Run PostgreSQL with Docker Compose.** Add a local database
  service, health check, named volume, and environment-based configuration.
- [ ] **Step 3.2 — Configure SQLAlchemy sessions and transactions.** Establish the
  engine, session lifecycle, and FastAPI dependency boundary.
- [ ] **Step 3.3 — Initialize Alembic.** Configure versioned schema migrations
  against the application's SQLAlchemy metadata.
- [ ] **Step 3.4 — Map and migrate aircraft data.** Add the first database model
  and review the generated migration before applying it.
- [ ] **Step 3.5 — Implement PostgreSQL aircraft persistence.** Replace the
  in-memory implementation through the existing boundary.
- [ ] **Step 3.6 — Add persistence integration tests.** Verify constraints,
  transactions, and create/get behavior against a test PostgreSQL database.

**Phase outcome:** aircraft data survives process restarts and database changes
are reproducible through reviewed migrations.

## Phase 4 — Model missions, waypoints, and routes

- [ ] **Step 4.1 — Define mission invariants and time semantics.** Decide mission
  fields, minimum waypoint count, coordinate rules, waypoint ordering, and UTC
  handling.
- [ ] **Step 4.2 — Implement mission and waypoint domain models.** Represent an
  ordered route without database or API dependencies.
- [ ] **Step 4.3 — Unit-test route invariants.** Cover coordinate boundaries,
  ordering, insufficient waypoints, and timezone requirements.
- [ ] **Step 4.4 — Map and migrate missions and waypoints.** Design relational
  ownership, order constraints, indexes, and foreign keys.
- [ ] **Step 4.5 — Implement mission persistence.** Store and reconstruct a
  mission while preserving its waypoint order.
- [ ] **Step 4.6 — Define mission API schemas and endpoints.** Add create and
  retrieve operations linked to an existing aircraft.
- [ ] **Step 4.7 — Add mission API and persistence tests.** Verify happy paths,
  validation, missing aircraft, ordering, and transaction behavior.

**Phase outcome:** clients can persist and retrieve a valid aircraft-linked
mission containing an ordered geographic route.

## Phase 5 — Integrate and normalize weather forecasts

- [ ] **Step 5.1 — Define the internal weather model.** Choose required metrics,
  units, timestamp rules, source metadata, and missing-data semantics.
- [ ] **Step 5.2 — Define the weather-provider interface.** Express what the
  application needs without exposing Open-Meteo response formats.
- [ ] **Step 5.3 — Explore and document the Open-Meteo contract.** Capture the
  selected endpoint, variables, units, resolution, limits, and error cases with
  representative fixtures.
- [ ] **Step 5.4 — Implement Open-Meteo response normalization.** Translate a
  saved provider response into the internal model before making live HTTP calls.
- [ ] **Step 5.5 — Unit-test weather normalization.** Cover normal, boundary,
  missing, malformed, and unit-related cases using local fixtures.
- [ ] **Step 5.6 — Add the live Open-Meteo client.** Configure an HTTP client with
  explicit timeouts, clear provider errors, and only justified retry behavior.
- [ ] **Step 5.7 — Test the provider adapter boundary.** Use mocked HTTP responses
  so automated tests remain deterministic and offline.
- [ ] **Step 5.8 — Design route sampling and timing.** Decide how segment
  locations and forecast times are selected, documenting accuracy limitations.
- [ ] **Step 5.9 — Retrieve weather for a mission route.** Orchestrate bounded
  provider requests and return normalized conditions for each segment.

**Phase outcome:** the application can obtain provider-independent forecast
conditions for an entire route without leaking Open-Meteo details into domain
logic.

## Phase 6 — Build the deterministic assessment engine

- [ ] **Step 6.1 — Specify constraint and warning rules.** Define inclusive
  boundaries, warning margins, missing-data behavior, units, and rule versioning
  before implementation.
- [ ] **Step 6.2 — Model constraint and segment results.** Create typed,
  explainable outcomes containing values, limits, margins, statuses, and reasons.
- [ ] **Step 6.3 — Implement one weather constraint evaluator.** Start with a
  single metric and keep the function pure.
- [ ] **Step 6.4 — Unit-test that evaluator thoroughly.** Cover safe, exact-limit,
  warning, unsafe, and missing-input cases.
- [ ] **Step 6.5 — Add the remaining constraint evaluators incrementally.** Add
  wind, gust, precipitation, and temperature rules with tests for each.
- [ ] **Step 6.6 — Aggregate constraints into a segment assessment.** Define
  severity precedence and deterministic reason ordering.
- [ ] **Step 6.7 — Aggregate segments into a mission assessment.** Produce the
  overall status and retain all supporting segment evidence.
- [ ] **Step 6.8 — Select and explain the limiting factor.** Implement a stable
  tie-break rule for breached limits or the smallest remaining margin.
- [ ] **Step 6.9 — Add scenario and edge-case tests.** Cover multi-segment routes,
  competing constraints, exact ties, and insufficient forecast data.

**Phase outcome:** normalized route weather produces a deterministic,
explainable segment-level and mission-level assessment.

## Phase 7 — Persist and expose assessments

- [ ] **Step 7.1 — Design assessment and snapshot persistence.** Decide what
  normalized inputs, results, provider metadata, and rule version must be kept
  for reproducibility.
- [ ] **Step 7.2 — Map and migrate weather snapshots.** Persist the immutable
  forecast input used by an assessment.
- [ ] **Step 7.3 — Map and migrate assessment results.** Persist mission and
  segment outcomes with reasons and the limiting factor.
- [ ] **Step 7.4 — Implement the assessment use case and transaction boundary.**
  Coordinate mission loading, weather retrieval, deterministic evaluation, and
  atomic persistence.
- [ ] **Step 7.5 — Expose assessment creation and retrieval endpoints.** Define
  request, response, status-code, and failure contracts.
- [ ] **Step 7.6 — Add assessment API integration tests.** Verify orchestration,
  persisted snapshots, deterministic results, retrieval, and provider failures.

**Phase outcome:** clients can request an assessment and later inspect the exact
forecast inputs, route outcomes, overall status, and explanation.

## Phase 8 — Recommend flight windows

- [ ] **Step 8.1 — Specify candidate-time and window semantics.** Define the
  search horizon, interval, mission-duration assumptions, suitability rule, and
  treatment of missing forecasts.
- [ ] **Step 8.2 — Evaluate a single alternative departure.** Reuse the existing
  assessment engine without duplicating its rules.
- [ ] **Step 8.3 — Evaluate a series of candidate departures.** Produce ordered,
  deterministic candidate results with bounded work.
- [ ] **Step 8.4 — Group suitable candidates into flight windows.** Convert
  adjacent acceptable times into intervals with explicit boundary semantics.
- [ ] **Step 8.5 — Rank and explain recommendations.** Add a deterministic ranking
  and report why recommended windows are preferable.
- [ ] **Step 8.6 — Expose the flight-window endpoint.** Add validated search
  parameters and a clear response contract.
- [ ] **Step 8.7 — Add flight-window unit and API tests.** Cover no window, one
  window, separated windows, ties, boundary times, and incomplete forecasts.

**Phase outcome:** clients can request and understand suitable departure windows
within a forecast period.

## Phase 9 — Harden the API and developer experience

- [ ] **Step 9.1 — Standardize API errors.** Provide consistent validation,
  not-found, conflict, provider, and internal error responses.
- [ ] **Step 9.2 — Add configuration management.** Validate environment settings
  and keep secrets out of source control and logs.
- [ ] **Step 9.3 — Add structured application logging.** Include request and
  assessment context without exposing sensitive values.
- [ ] **Step 9.4 — Separate liveness and readiness checks.** Make readiness
  reflect required dependencies without overloading the database or provider.
- [ ] **Step 9.5 — Review OpenAPI and API consistency.** Refine naming, examples,
  pagination where needed, response codes, and endpoint documentation.
- [ ] **Step 9.6 — Add end-to-end MVP tests.** Exercise the main workflow through
  the API with controlled provider data and PostgreSQL.
- [ ] **Step 9.7 — Complete project and architecture documentation.** Add setup,
  diagrams, domain decisions, limitations, example requests, and troubleshooting.

**Phase outcome:** the complete local MVP is consistent, observable, documented,
and demonstrable.

## Phase 10 — Containerize and automate CI

- [ ] **Step 10.1 — Create the production API image.** Add a non-root, minimal
  Docker build with pinned dependencies and a clear startup command.
- [ ] **Step 10.2 — Complete the Docker Compose environment.** Run the API and
  PostgreSQL together with health checks and explicit configuration.
- [ ] **Step 10.3 — Verify migrations in the container workflow.** Document and
  test when and how schema migrations run.
- [ ] **Step 10.4 — Add the GitHub Actions quality workflow.** Run formatting,
  linting, type checking, and unit tests on supported pull-request changes.
- [ ] **Step 10.5 — Add CI integration tests with PostgreSQL.** Use a service
  database and deterministic weather fixtures.
- [ ] **Step 10.6 — Add image build verification.** Ensure the deployable image
  builds after quality and test checks pass.

**Phase outcome:** a clean checkout can be tested and built reproducibly by CI.

## Phase 11 — Deploy the MVP to AWS

- [ ] **Step 11.1 — Produce the AWS deployment design and cost estimate.** Define
  networking, environments, secrets, IAM boundaries, migration strategy,
  rollback, and expected portfolio-scale costs before provisioning.
- [ ] **Step 11.2 — Provision ECR and publish a versioned image.** Use immutable
  identifiers and document the build-to-registry path.
- [ ] **Step 11.3 — Provision RDS PostgreSQL securely.** Configure private
  connectivity, credentials, backups, and restricted network access.
- [ ] **Step 11.4 — Create the ECS Fargate service.** Configure the task, service,
  networking, health checks, environment, and least-privilege task roles.
- [ ] **Step 11.5 — Configure CloudWatch logging and basic alarms.** Make startup,
  request failures, and resource issues diagnosable.
- [ ] **Step 11.6 — Run production migrations safely.** Apply the reviewed schema
  with a repeatable one-off deployment procedure.
- [ ] **Step 11.7 — Add the public HTTPS entry point.** Configure the load
  balancer, TLS certificate, DNS if available, and appropriate security groups.
- [ ] **Step 11.8 — Perform deployment smoke and failure tests.** Verify health,
  the core assessment workflow, log visibility, restart behavior, and database
  persistence.
- [ ] **Step 11.9 — Document deployment and rollback.** Record operations,
  configuration, cost controls, limitations, and teardown instructions.

**Phase outcome:** the tested API runs on ECS Fargate with RDS PostgreSQL,
versioned images in ECR, HTTPS access, and useful CloudWatch visibility.

## Phase 12 — Final portfolio review

- [ ] **Step 12.1 — Audit the MVP against `PROJECT.md`.** Confirm every claimed
  capability exists and remove or label anything incomplete.
- [ ] **Step 12.2 — Review architecture and code quality.** Check dependency
  boundaries, naming, typing, migrations, tests, and unresolved technical debt.
- [ ] **Step 12.3 — Review reliability and security basics.** Check secrets,
  dependency findings, container privileges, IAM, database exposure, and error
  leakage.
- [ ] **Step 12.4 — Prepare the portfolio demonstration.** Create a reproducible
  scenario that shows aircraft setup, a route assessment, explanations, and a
  recommended window.
- [ ] **Step 12.5 — Prepare interview explanations.** Summarize key tradeoffs,
  alternatives rejected, difficult bugs, testing strategy, and future scaling
  choices.

**Phase outcome:** the repository makes accurate claims, demonstrates a complete
production-quality MVP, and can be confidently explained in an interview.

## Deferred extensions

These are intentionally outside the roadmap until Phase 12 is complete:

- PostGIS and advanced geospatial analysis.
- AWS CDK or another infrastructure-as-code tool.
- React/TypeScript frontend and map visualization.
- Redis and background jobs.
- Restricted/no-fly-zone integration.
- Historical operational analytics.
- Additional weather providers.
- Authentication and multi-tenancy.
