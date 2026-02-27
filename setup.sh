#!/bin/bash

echo "============================================================"
echo "  FINTECH CORE - Production-Grade Django Wallet Backend"
echo "============================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "OK: Created .env file. Please review and update if needed."
    echo ""
fi

echo "Starting setup process..."
echo ""

# Build containers
echo "Building Docker containers..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "OK: Build completed successfully."
echo ""

# Start services
echo "Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start services. Please check the error messages above."
    exit 1
fi

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Run migrations
echo ""
echo "Running database migrations..."
docker-compose exec web python manage.py migrate

if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "OK: Migrations completed successfully."
echo ""

# Check if superuser exists
echo "Checking for superuser..."
SUPERUSER_EXISTS=$(docker-compose exec -T web python manage.py shell -c "from users.models import User; print(User.objects.filter(is_superuser=True).exists())")

if [[ $SUPERUSER_EXISTS == *"True"* ]]; then
    echo "OK: Superuser already exists."
else
    echo ""
    echo "Creating superuser..."
    echo "Please provide superuser details:"
    docker-compose exec web python manage.py createsuperuser
fi

echo ""
echo "============================================================"
echo "  SETUP COMPLETE"
echo "============================================================"
echo ""
echo "Services Status:"
docker-compose ps
echo ""
echo "Access Points:"
echo "   • API:           http://localhost:8000"
echo "   • Admin:         http://localhost:8000/admin/"
echo "   • Health Check:  http://localhost:8000/api/health/"
echo "   • API Docs:      See API_DOCUMENTATION.md"
echo ""
echo "Quick Commands:"
echo "   • View logs:     docker-compose logs -f"
echo "   • Stop:          docker-compose down"
echo "   • Restart:       docker-compose restart"
echo "   • Run tests:     docker-compose exec web pytest -v"
echo "   • Django shell:  docker-compose exec web python manage.py shell"
echo ""
echo "Using Makefile:"
echo "   • make help      - See all available commands"
echo "   • make logs      - View logs"
echo "   • make test      - Run tests"
echo "   • make shell     - Open Django shell"
echo ""
echo "Happy coding."
