.PHONY: help sync lint format migrate docker-up docker-down docker-build-up logs clean

help:
	@echo "Wallet API - Available commands:"
	@echo ""
	@echo "    make lint       - Code style check (ruff)"
	@echo "    make format     - Format code (ruff)"
	@echo ""
	@echo "    make db-migrate - Apply migrations"
	@echo ""
	@echo "    make docker-up   - Start all services (DB + app)"
	@echo "    make docker-down - Stop all services"

sync:
	uv sync

lint:
	ruff check app/

format:
	ruff format app/

db-migrate:
	alembic upgrade head

docker-build-up:
	docker-compose build
	docker-compose up

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

logs:
	docker-compose logs -f app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache