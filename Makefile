.PHONY: dev build up down logs test lint format tf-validate tf-plan clean

dev:
	docker compose up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint
	cd terraform && terraform fmt -check -recursive

format:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd terraform && terraform fmt -recursive

tf-validate:
	cd terraform && terraform validate
	cd terraform/bootstrap && terraform validate

tf-plan:
	cd terraform && terraform plan

clean:
	rm -rf frontend/dist backend/.pytest_cache backend/.ruff_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
