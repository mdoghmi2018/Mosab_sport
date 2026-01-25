.PHONY: help up down build logs ps health seed test e2e clean

help:
	@echo "Mosab Sport - Development Commands"
	@echo ""
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Build and start services"
	@echo "  make logs        - Show logs from all services"
	@echo "  make ps          - Show service status"
	@echo "  make health      - Check API health"
	@echo "  make seed        - Seed demo data"
	@echo "  make test        - Run E2E smoke test"
	@echo "  make e2e         - Full golden routine + E2E test"
	@echo "  make clean       - Stop and remove volumes"
	@echo ""

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

logs:
	docker-compose logs -f

ps:
	docker-compose ps

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not reachable"

seed:
	@echo "🌱 Seeding demo data..."
	docker-compose exec -T api python3 /app/scripts/seed_demo_data.py || \
	python3 scripts/seed_demo_data.py

test:
	@echo "🧪 Running E2E smoke test..."
	python3 scripts/e2e_smoke_test.py

e2e:
	@echo "🚀 Running full golden routine..."
	@bash scripts/golden_routine.sh
	@echo ""
	@echo "🌱 Seeding demo data..."
	@python3 scripts/seed_demo_data.py
	@echo ""
	@echo "🧪 Running E2E smoke test..."
	@python3 scripts/e2e_smoke_test.py

clean:
	docker-compose down -v

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(MESSAGE)"

shell-api:
	docker-compose exec api /bin/bash

shell-db:
	docker-compose exec db psql -U mosab_user -d mosab_sport

