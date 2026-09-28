# Interview guide

## Architecture in one minute

FlightOps is a modular monolith with a Vue client and one FastAPI deployment.
Routes validate and translate HTTP; application services orchestrate use cases;
pure domain code evaluates deterministic rules; SQLAlchemy persists normalized
inputs and versioned outputs; and an adapter converts Open-Meteo data into an
internal weather model. This keeps the system simple to operate while retaining
boundaries that are independently testable.

## Decisions and tradeoffs

### Why a modular monolith?

The domain and expected load do not justify distributed transactions, multiple
deployments, or service-to-service failure modes. Module boundaries preserve a
future extraction path without paying microservice complexity now.

### Why store weather snapshots?

Forecasts change. Re-fetching later could produce a different answer and make an
old decision impossible to explain. Persisting normalized inputs plus a rule
version makes the assessment auditable and deterministic.

### Why JSON for assessment evidence?

Evidence is written and read as one versioned document. Mission ID, status,
departure, and limiting factor remain indexed relational columns. If analytics
over individual constraints becomes a real requirement, those results can be
normalized in a later migration.

### Why dependency injection?

Database sessions and the weather provider sit at side-effect boundaries.
Injecting them gives tests deterministic forecast data and isolated database
transactions without putting test branches in production code.

### Why UTC and timezone-aware input?

A naive local time is ambiguous across user locations and daylight-saving
changes. The API requires an offset and converts instants to UTC for storage and
comparison.

### Why CloudFront, ALB, and Fargate?

CloudFront provides an AWS-managed HTTPS hostname without requiring the student
to own a domain and serves the private S3 Vue build. ALB performs ECS health
routing. Fargate demonstrates container operations without managing EC2 hosts.
For a very small commercial product, App Runner or Lambda could cost less and
would be reasonable alternatives.

### Why is the task in a public subnet?

Open-Meteo and ECR require outbound access. A NAT gateway or a set of VPC
endpoints costs more than this portfolio workload. The task therefore has a
public IP but its security group permits inbound traffic only from the ALB.
Private subnets are the preferred production hardening step.

### What would you improve next?

Authentication, authorization, rate limiting, private task networking,
Multi-AZ RDS, alarm notifications, route traversal timing, richer provider
resilience, no-fly-zone data, and map visualization—only after validating the
actual need.

## Testing explanation

- Pure unit tests exercise domain invariants and risk boundaries.
- Normalization tests cover provider data without network access.
- Mocked HTTP tests verify adapter success and failure translation.
- API tests run the complete use case with a controllable provider and database.
- A CI integration test runs against migrated PostgreSQL.
- Vue has a UI smoke test, strict type checking, and a production build check.
- Docker images and CloudFormation templates are built or linted in CI.

## Difficult engineering details

- Stable worst-severity aggregation and tie-breaking.
- Fail-closed treatment of missing or out-of-range forecast data.
- Preserving ordered waypoints in both relational storage and API output.
- Atomic persistence of assessment output and its exact input snapshot.
- Separating liveness from dependency-aware readiness.
- Running migrations once as an ECS task instead of racing at container startup.
