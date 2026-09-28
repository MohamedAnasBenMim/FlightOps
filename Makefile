.PHONY: quality test infra frontend compose-up migrate

quality:
	.venv/bin/ruff format --check .
	.venv/bin/ruff check .
	.venv/bin/mypy

test:
	.venv/bin/pytest -q

infra:
	.venv/bin/cfn-lint deploy/aws/bootstrap.yml deploy/aws/infrastructure.yml
	bash -n deploy/aws/*.sh

frontend:
	cd frontend && npm test && npm run build

compose-up:
	docker compose up --build -d

migrate:
	docker compose run --rm api alembic upgrade head
