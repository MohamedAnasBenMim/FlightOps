# MVP audit

Audit date: 2026-09-28.

## Capability audit

| Claim | Evidence | Status |
| --- | --- | --- |
| Aircraft limits | Domain model, API, database constraints, tests | Complete |
| Ordered missions | Waypoint constraints, ordered relationship, API tests | Complete |
| Weather integration | Provider protocol, Open-Meteo adapter, mocked and live smoke tests | Complete |
| Explainable risk | Pure versioned rules and segment evidence | Complete |
| Persisted assessment | Atomic snapshot/result transaction and retrieval test | Complete |
| Flight windows | Bounded candidate evaluation and grouping tests | Complete |
| Vue workflow | Typed dashboard, UI test, production build | Complete |
| PostgreSQL | Alembic migration, Compose smoke, CI integration test | Complete |
| Containers and CI | Non-root images, health checks, GitHub Actions | Complete |
| AWS deployment | Validated templates and guarded automation | Ready, not provisioned |
| Live AWS verification | Requires valid AWS credentials and a billable deployment | Blocked |

## Code-quality audit

- Domain code has no FastAPI, SQLAlchemy, or Open-Meteo response dependency.
- Side effects sit behind session and provider boundaries.
- Timestamps are timezone-aware at the API edge and normalized to UTC.
- Database and provider failures produce stable HTTP errors.
- Migration metadata and PostgreSQL schema report no drift locally.
- Python linting, formatting, strict typing, and tests pass.
- Vue typing, tests, build, and npm audit pass.
- CloudFormation templates pass cfn-lint.
- The repository contains no committed .env file or generated build cache.

## Known debt

- Authentication and rate limiting are absent by explicit MVP scope.
- Segment sampling does not model travel time.
- Flight-window searches call the provider once per candidate and segment; a
  batched forecast query is the first performance improvement to investigate.
- Constraint evidence in JSON is not optimized for cross-mission analytics.
- The third-party Starlette test client emits an AnyIO deprecation warning.
- Live AWS claims must remain disabled until provisioning and verification pass.

## Final acceptance gate

The repository may be described as a complete local and deployment-ready MVP.
It must not be described as live on AWS until every Phase 11 provisioning box in
ROADMAP.md is supported by real account evidence.
