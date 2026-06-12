.PHONY: up down test seed lint typecheck

up:
	docker compose up -d

down:
	docker compose down

test:
	cd backend && python -m pytest -q
	cd frontend && npm run test -- --run

seed:
	docker compose exec backend python scripts/seed_admin.py

lint:
	cd backend && ruff check .
	cd frontend && npx eslint .

typecheck:
	cd backend && mypy app
	cd frontend && npx tsc --noEmit
