.PHONY: dev dev-backend dev-frontend test test-backend test-frontend lint migrate seed

dev:
	docker compose up

dev-backend:
	cd backend && python manage.py runserver

dev-frontend:
	cd frontend && npm run dev

migrate:
	cd backend && python manage.py migrate

seed:
	cd backend && python manage.py seed_dev

test:
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run test

lint:
	cd backend && ruff check . && black --check .
	cd frontend && npm run lint

double-migrate:
	cd backend && python manage.py migrate && python manage.py migrate
