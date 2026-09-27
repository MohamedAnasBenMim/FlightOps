.PHONY: quality test frontend compose-up migrate

quality:
	.venv/bin/ruff format --check .
	.venv/bin/ruff check .
	.venv/bin/mypy

test:
	.venv/bin/pytest -q

frontend:
	cd frontend && npm test && npm run build

compose-up:
	docker compose up --build -d

migrate:
	docker compose run --rm api alembic upgrade head
