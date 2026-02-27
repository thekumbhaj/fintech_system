# Fintech Core - Django Wallet Backend

Production-grade fintech wallet backend built with Django, PostgreSQL, Redis, and Celery. This system enforces atomic money operations, row-level locking, idempotency, and a clear audit trail.

## Stack

- Django 4.2 + Django REST Framework
- PostgreSQL 15
- Redis 7 (cache + Celery broker)
- Celery 5
- JWT authentication (SimpleJWT)
- Docker + Docker Compose
- Devcontainer for GitHub Codespaces

## Apps

- users: custom User model, email login, phone, KYC workflow
- wallet: one-to-one wallet with Decimal balance, auto-created via signals
- transactions: transfers, ledger entries, idempotency, audit trail
- payments: payment intent simulation and webhook processing

## Project Structure

```
fintech_system/
  fintech_core/
    settings.py
    urls.py
    celery.py
    middleware.py
    exceptions.py
    views.py
  users/
    models.py
    serializers.py
    views.py
    urls.py
    signals.py
  wallet/
    models.py
    serializers.py
    views.py
    urls.py
    signals.py
  transactions/
    models.py
    serializers.py
    services.py
    views.py
    urls.py
    tests.py
  payments/
    models.py
    serializers.py
    services.py
    tasks.py
    views.py
    urls.py
  docker-compose.yml
  Dockerfile
  requirements.txt
  .env.example
  entrypoint.sh
  manage.py
```

## Setup (Codespaces)

1. Copy environment variables:

```
cp .env.example .env
```

2. Build and start services:

```
docker-compose up -d --build
```

3. Run migrations:

```
docker-compose exec web python manage.py migrate
```

4. Create a superuser:

```
docker-compose exec web python manage.py createsuperuser
```

5. Health check:

```
curl http://localhost:8000/api/health/
```

## Example API Flow

Login:

```
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'
```

Transfer:

```
curl -X POST http://localhost:8000/api/transactions/transactions/transfer/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_user_email":"recipient@example.com","amount":"50.00","description":"Payment","idempotency_key":"txn-123"}'
```

## Notes

- Money values use DecimalField and are processed in atomic blocks.
- Transfers lock wallets with select_for_update to prevent race conditions.
- Idempotency is enforced with unique reference IDs and cache lookups.

## Architecture (Brief)

The system is split into four apps with a thin HTTP layer and a service layer for financial operations. TransactionService and PaymentService encapsulate business logic and perform atomic, row-locked updates. Redis handles caching and Celery messaging, while PostgreSQL provides strong consistency and indexed query performance. JWT auth secures API access, and middleware provides request logging for traceability.