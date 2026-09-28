# Portfolio demonstration

## Five-minute scenario

Start the local stack and migrate it:

~~~bash
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d --wait
~~~

Open <http://localhost:18080>.

1. Create an aircraft named Demo Surveyor with 12 m/s wind, 18 m/s gust,
   2 mm/h precipitation, and -10 to 45 °C limits.
2. Create a mission for tomorrow with three waypoints around Tunis.
3. Run the assessment and show the overall status, limiting factor, rule
   version, per-segment constraints, and stored forecast-point count.
4. Request candidate departures at one-hour intervals.
5. Open <http://localhost:18000/docs> and retrieve the same assessment by ID.
6. Restart only the API container and retrieve it again to demonstrate
   PostgreSQL persistence.

## What to narrate

- The dashboard is a client; it does not contain safety rules.
- Pydantic validates the HTTP boundary while domain dataclasses protect
  framework-independent invariants.
- The provider adapter isolates Open-Meteo response shapes from the risk engine.
- Risk functions are pure and deterministic.
- The stored snapshot explains exactly which normalized forecast drove a result.
- Alembic versions schema changes; SQLAlchemy sessions define transaction
  boundaries.
- Unit tests cover rules, API tests control provider input, and CI adds a real
  PostgreSQL integration test.
- The deployment uses immutable images and a one-off migration task.

## Honest limitations to show

Route segments use midpoint weather at a common candidate departure, not
high-resolution interpolation or traversal-time modelling. FlightOps does not
analyze airspace, terrain, battery, payload, communication links, or legal
authorization. It is decision support, not a safety guarantee.
