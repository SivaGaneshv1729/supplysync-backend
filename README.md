# SupplySync

SupplySync is an enterprise-grade Django backend for inventory, procurement, sales, and warehouse operations. It provides REST APIs for managing products, warehouses, inventory, purchase orders, sales orders, suppliers, and operational reports.

## What is SupplySync?

SupplySync helps businesses:

- Track warehouse inventory across multiple locations
- Create, approve, receive, and cancel purchase orders
- Create, dispatch, deliver, and cancel sales orders
- Maintain supplier and product catalogs
- Automatically process inventory transactions and low-stock alerts
- Authenticate users with JWT access and refresh tokens

## Key Technologies

- Python 3.13
- Django 5.x
- Django REST Framework
- djangorestframework-simplejwt
- Celery + django-celery-beat
- Redis for caching, broker, and token blacklist
- PostgreSQL for production
- SQLite for testing
- Pytest + pytest-django for automated tests

## Documentation

This repository includes detailed documentation in the `docs/` folder:

- `docs/architecture.md` — system architecture, flow charts, and component responsibilities
- `docs/developer-guide.md` — setup, run, test, and development workflow

## Project Structure

- `apps/` — application modules and business logic
- `core/` — shared models, exceptions, pagination, permissions, and throttles
- `supplysync/` — project settings and entrypoints
- `tests/` — pytest test suite for APIs and services
- `docker-compose.yml` — local infrastructure composition

## Quick Start

### 1. Clone and enter repo

```bash
git clone <repository_url>
cd supplysync
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start infrastructure with Docker

```bash
docker-compose up -d postgres redis
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Start the Django server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## Docker Compose Services

The repository includes a Docker Compose configuration for local development:

- `postgres` — PostgreSQL database
- `redis` — Redis cache/broker
- `celery_worker` — Celery worker for background tasks
- `celery_beat` — Celery beat scheduler for periodic tasks

Start the full stack:

```bash
docker-compose up -d
```

Stop all services:

```bash
docker-compose down
```

## Environment & Settings

### Development settings

The project default uses `supplysync.settings.development`.

### Testing settings

Pytest uses `supplysync.settings.testing` defined in `pytest.ini`.

### Important variables

- `SECRET_KEY` — replace in production
- `DATABASES` — configure PostgreSQL in production
- `CELERY_BROKER_URL` — Redis broker URL
- `CELERY_RESULT_BACKEND` — Redis result backend
- `CACHES` — Redis cache for local/production

## Authentication Flow

SupplySync uses JWT authentication with access and refresh tokens.

### Authentication endpoints

- `POST /api/v1/auth/register/` — create a new user and return JWT tokens
- `POST /api/v1/auth/login/` — authenticate credentials and return JWT tokens
- `POST /api/v1/auth/token/refresh/` — refresh access token using a refresh token
- `POST /api/v1/auth/logout/` — blacklist a refresh token
- `POST /api/v1/auth/change-password/` — change authenticated user password

### Login behavior

1. User submits email and password
2. Credentials are verified
3. On success, JWT access and refresh tokens are returned
4. On invalid credentials, the response returns `401 Unauthorized`

## Testing

Run the full test suite:

```bash
python -m pytest -q
```

Run a specific test file:

```bash
python -m pytest tests/test_accounts/test_views.py -q
```

Run a targeted test method:

```bash
python -m pytest tests/test_sales_orders/test_services.py::test_cancel_sales_order_releases_reserved_inventory -q
```

### Notes

- Tests use SQLite via `supplysync.settings.testing`
- Celery tasks are executed eagerly during tests
- `pytest.ini` holds the Django settings and test discovery rules

## Architecture Overview

SupplySync is designed as a modular backend with the following responsibilities:

- `apps/accounts/` — authentication, registration, password management
- `apps/products/` — product catalog, pricing, SKU management
- `apps/warehouses/` — warehouse metadata and filters
- `apps/inventory/` — stock tracking, transactions, reservation management
- `apps/purchase_orders/` — purchase order creation, approval, receiving, cancellation
- `apps/sales_orders/` — sales order creation, dispatch, delivery, cancellation
- `apps/suppliers/` — supplier catalog management
- `apps/reports/` — operational reports and summaries

For full architectural details and flow charts, see `docs/architecture.md`.

## Common Commands

```bash
# Start project server
python manage.py runserver

# Run database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run Celery worker locally
celery -A supplysync worker -l info

# Run Celery beat locally
celery -A supplysync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Run tests
python -m pytest -q
```

## Contribution

1. Create a new branch for the feature or fix
2. Run tests locally
3. Update documentation if behavior changes
4. Commit with a descriptive message
5. Push to remote and create a pull request

---

For more details, open the developer docs in `docs/developer-guide.md` and system architecture in `docs/architecture.md`.
