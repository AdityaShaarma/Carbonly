.PHONY: install migrate seed run test lint format docker-up docker-down

install:
	pip install -r requirements.txt

migrate:
	alembic upgrade head

seed:
	python scripts/seed_dev.py

run:
	uvicorn app.main:app --reload

test:
	pytest tests/ -v

lint:
	ruff check app tests

format:
	black app tests

docker-up:
	docker compose up -d

docker-down:
	docker compose down
