.PHONY: dev build up down logs test lint format tf-validate tf-plan clean

backend/.env:
	cp backend/.env.example backend/.env

dev: backend/.env
	docker compose up

build:
	docker compose build

up: backend/.env
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	cd backend && uv run pytest -q

frontend/node_modules:
	cd frontend && npm ci

lint: frontend/node_modules
	cd backend && uv run ruff check .
	cd frontend && npm run lint
	cd terraform && terraform fmt -check -recursive

format:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd terraform && terraform fmt -recursive

tf-validate:
	cd terraform && terraform init -backend=false -input=false >/dev/null && terraform validate
	cd terraform/bootstrap && terraform init -backend=false -input=false >/dev/null && terraform validate

tf-plan:
	cd terraform && terraform plan

clean:
	rm -rf frontend/dist backend/.pytest_cache backend/.ruff_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
