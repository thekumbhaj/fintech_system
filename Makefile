.PHONY: help build up down restart logs migrations migrate shell test clean superuser

help:
	@echo "Fintech Core - Django Wallet Backend"
	@echo ""
	@echo "Available commands:"
	@echo "  make build        - Build Docker containers"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs (all services)"
	@echo "  make migrations   - Create database migrations"
	@echo "  make migrate      - Run database migrations"
	@echo "  make shell        - Open Django shell"
	@echo "  make test         - Run tests"
	@echo "  make superuser    - Create superuser"
	@echo "  make clean        - Remove containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

migrations:
	docker-compose exec web python manage.py makemigrations

migrate:
	docker-compose exec web python manage.py migrate

shell:
	docker-compose exec web python manage.py shell

test:
	docker-compose exec web pytest -v

superuser:
	docker-compose exec web python manage.py createsuperuser

clean:
	docker-compose down -v
	rm -rf logs/*.log

# Initial setup
setup: build
	docker-compose up -d
	sleep 5
	docker-compose exec web python manage.py migrate
	@echo ""
	@echo "Setup complete! Create a superuser with: make superuser"
	@echo "Access the API at: http://localhost:8000"
