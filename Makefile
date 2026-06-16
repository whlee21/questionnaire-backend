.PHONY: up down test seed lint typecheck migrate makemigrations

up:
	podman compose up -d

down:
	podman compose down

test:
	cd backend && python -m pytest -q
	cd frontend && npm run test -- --run

seed:
	podman compose exec backend python scripts/seed_admin.py

lint:
	cd backend && ruff check .
	cd frontend && npx eslint .

typecheck:
	cd backend && mypy app
	cd frontend && npx tsc --noEmit

migrate:
	cd backend && alembic upgrade head

makemigrations:
	cd backend && alembic revision --autogenerate -m "$(MSG)"
