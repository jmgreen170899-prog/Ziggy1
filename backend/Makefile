# Ziggy Clean – Backend Makefile

.SILENT:

PY=python
POETRY=poetry

# --- Backend setup ---
install:
	cd backend && $(POETRY) install

run:
	cd backend && $(POETRY) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	cd backend && $(POETRY) run ruff check .
	cd backend && $(POETRY) run mypy app || true

test:
	cd backend && $(POETRY) run pytest -q

freeze:
	cd backend && $(POETRY) export -f requirements.txt --without-hashes -o requirements-merged.txt

# --- Docker helpers (root-level docker-compose) ---
up:
	docker compose up --build

down:
	docker compose down

.PHONY: install run lint test freeze up down
