# SupplySync

SupplySync is a Django-based inventory and order management backend focused on warehouse, procurement, and fulfillment workflows.

## Overview

SupplySync provides REST APIs for product and warehouse inventory tracking, purchase order management, sales order fulfillment, and operational reporting.

This project is built with:

- Django
- Django REST Framework
- Celery
- Redis
- PostgreSQL (production)

## Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd supplysync
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the infrastructure**
   Make sure you have Docker installed and running. Start PostgreSQL and Redis:
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start Celery worker and beat**
   You can run Celery using Docker Compose or locally.

   To start Celery via Docker:
   ```bash
   docker-compose up -d celery_worker celery_beat
   ```

   To run locally:
   ```bash
   celery -A supplysync worker -l info
   celery -A supplysync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

7. **Create an admin user (optional)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start the Django development server**
   ```bash
   python manage.py runserver
   ```

9. **Run tests**
   ```bash
   pytest
   ```

## Development Notes

- `manage.py` uses `supplysync.settings.development` by default.
- Run `python manage.py check` to validate Django configuration.
- For local reset, remove `db.sqlite3` and re-run migrations.
