# Developer Guide

This document explains how to set up SupplySync for development, run services, and execute tests.

## Prerequisites

- Python 3.13
- Docker and Docker Compose
- Git
- A terminal with access to `python` and `pip`

## Local Environment Setup

### 1. Clone the repository

```bash
git clone <repository_url>
cd supplysync
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

- Windows:

```powershell
venv\Scripts\activate
```

- macOS / Linux:

```bash
source venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## Running the Application Locally

### Start PostgreSQL and Redis with Docker

```bash
docker-compose up -d postgres redis
```

### Apply database migrations

```bash
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

### Run the Django development server

```bash
python manage.py runserver
```

The API will be accessible on `http://127.0.0.1:8000/`.

## Running Celery

### Start worker locally

```bash
celery -A supplysync worker -l info
```

### Start beat scheduler locally

```bash
celery -A supplysync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Start Celery with Docker Compose

```bash
docker-compose up -d celery_worker celery_beat
```

## API Testing and Development

### Run the full test suite

```bash
python -m pytest -q
```

### Run a specific test file

```bash
python -m pytest tests/test_accounts/test_views.py -q
```

### Run a targeted test method

```bash
python -m pytest tests/test_sales_orders/test_services.py::test_cancel_sales_order_releases_reserved_inventory -q
```

### Common test flags

- `-q`: quiet output
- `-vv`: verbose output
- `--maxfail=1`: stop on first failure

## Working with Settings

### Production

Configure `supplysync.settings.production` for production deployment.

### Development

Use `supplysync.settings.development` for local development.

### Testing

Pytest uses the testing settings defined in `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = supplysync.settings.testing
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v
```

## Branching and Commit Workflow

1. Create a feature branch:

```bash
git checkout -b feature/your-change
```

2. Make code or documentation changes
3. Run tests locally
4. Stage and commit changes

```bash
git add .
git commit -m "docs: add detailed README and developer documentation"
```

5. Push to remote:

```bash
git push origin feature/your-change
```

## Recommended Workflow

1. Run `python -m pytest -q` before committing
2. Keep documentation in sync with API and feature changes
3. Use `git status` and `git diff` to review changes
4. Add new tests for new behavior

## Useful Commands

```bash
# Start development server
python manage.py runserver

# Check Django configuration
python manage.py check

# Run migrations
python manage.py migrate

# Launch shell
python manage.py shell

# Run a single Django test
python -m pytest tests/test_inventory/test_inventory_services.py -q
```

## Notes

- The repository is intentionally structured to separate API views, serializers, and service-layer business logic.
- Background jobs are decoupled from API handling using Celery tasks.
- Redis is used for caching, token blacklisting, and rate limiting.
- JWT tokens are used for authentication to support stateless API sessions.
