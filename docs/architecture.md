# SupplySync Architecture

This document describes how SupplySync is organized, how data and workflows move through the backend, and how the various subsystems interact.

## System Overview

SupplySync is a service-oriented Django backend with REST APIs and background processing via Celery.

- **Web API layer**: Django + Django REST Framework
- **Authentication**: JWT access/refresh tokens using `djangorestframework-simplejwt`
- **Background tasks**: Celery workers and Celery Beat
- **Cache and broker**: Redis
- **Primary database**: PostgreSQL in production, SQLite for testing

## Component Map

- `apps/accounts`: user registration, authentication, password management
- `apps/products`: product catalog, SKU management, pricing
- `apps/warehouses`: warehouse metadata, filters, and lookup
- `apps/inventory`: inventory levels, reserved quantity, transaction audit
- `apps/purchase_orders`: purchase order lifecycle
- `apps/sales_orders`: sales order lifecycle
- `apps/suppliers`: supplier metadata and contact information
- `apps/reports`: runtime reports and reporting endpoints
- `core`: shared helpers, exceptions, pagination, throttling, permissions

## 🗄️ Database Schema (ERD)

The following diagram represents the core entities and their relationships. All models inherit from a `BaseModel` providing `created_at`, `updated_at`, and soft-delete capabilities.

```mermaid
erDiagram
    USER ||--o{ PURCHASE_ORDER : "creates/approves"
    USER ||--o{ SALES_ORDER : "creates"
    USER ||--o{ INVENTORY_TRANSACTION : "performs"
    
    WAREHOUSE ||--o{ INVENTORY : "contains"
    WAREHOUSE ||--o{ PURCHASE_ORDER : "ships to"
    WAREHOUSE ||--o{ SALES_ORDER : "ships from"
    
    PRODUCT ||--o{ INVENTORY : "stored as"
    PRODUCT ||--o{ PURCHASE_ORDER_ITEM : "ordered in"
    PRODUCT ||--o{ SALES_ORDER_ITEM : "sold in"
    CATEGORY ||--o{ PRODUCT : "categorizes"
    
    SUPPLIER ||--o{ PURCHASE_ORDER : "supplies"
    
    PURCHASE_ORDER ||--|{ PURCHASE_ORDER_ITEM : "contains"
    SALES_ORDER ||--|{ SALES_ORDER_ITEM : "contains"
    
    INVENTORY ||--o{ INVENTORY_TRANSACTION : "tracked by"
```

## High-Level Flow Charts

### 1. User Authentication Flow

```mermaid
flowchart TD
    A[Client submits login request] --> B[LoginView validates credentials]
    B --> C[authenticate(email, password)]
    C -->|valid| D[login_user service updates last login and issues tokens]
    D --> E[Return access_token + refresh_token]
    C -->|invalid| F[Return 401 NOT_AUTHENTICATED]
```

### 2. Purchase Order Lifecycle

```mermaid
flowchart LR
    A[Create PO request] --> B[create_purchase_order service]
    B --> C[Create PO record in DRAFT status]
    C --> D[Add PO line items]
    D --> E[Submit PO request]
    E --> F[submit_purchase_order changes status to PENDING_APPROVAL]
    F --> G[approve_purchase_order changes status to APPROVED]
    G --> H[receive_purchase_order processes inbound receipt]
    H --> I[Inventory is adjusted, PO status becomes RECEIVED or PARTIALLY_RECEIVED]
    F --> J[cancel_purchase_order allowed if DRAFT/PENDING_APPROVAL/APPROVED]
```

### 3. Sales Order Lifecycle

```mermaid
flowchart LR
    A[Create sales order] --> B[create_sales_order validates inventory]
    B --> C[Reserve inventory quantity]
    C --> D[Create SO in PENDING status]
    D --> E[dispatch_sales_order releases reserved inventory and creates outbound transactions]
    E --> F[SO status becomes DISPATCHED]
    F --> G[deliver_sales_order sets status to DELIVERED]
    D --> H[cancel_sales_order allowed when PENDING or CONFIRMED]
```

### 4. Inventory Transaction Flow

```mermaid
flowchart TD
    A[Purchase receipt or inventory adjustment] --> B[apps.inventory.services.adjust_inventory]
    B --> C[Create InventoryTransaction record]
    C --> D[Update warehouse inventory quantities]
    D --> E[Optional low-stock alert and report updates]
```

## Data Flow and Responsibilities

### Authentication and Authorization

- `apps/accounts/views.py` handles API requests.
- `apps/accounts/serializers.py` validates payloads.
- `apps/accounts/services.py` performs business logic and token generation.
- `core/throttles.py` enforces login rate limiting.
- `core/exceptions.py` standardizes API errors.

### Purchase Order Processing

- `apps/purchase_orders/services.py` orchestrates PO creation, submission, approval, receiving, and cancellation.
- Incoming receipt operations adjust inventory through `apps.inventory.services.adjust_inventory`.
- Purchase order receiving triggers a background task via `process_purchase_order_received_event`.

### Sales Order Processing

- `apps/sales_orders/services.py` validates stock before order creation.
- Inventory is reserved at order creation and released on cancellation or dispatch.
- Dispatch and delivery actions update order status and create inventory transaction records.
- `process_sales_order_created_event` and `process_sales_order_cancelled_event` are asynchronous task hooks.

## Error Handling

SupplySync uses a centralized exception handler in `core/exceptions.py` that returns a unified response shape:

- `timestamp`
- `status`
- `error_code`
- `message`
- `path`
- `errors`

This provides consistent API responses for validation failures, authentication errors, resource not found, invalid operations, and internal errors.

## Notes on the Service Layer

- Core business logic lives in `services.py` modules inside each app.
- Views delegate validation and request handling to serializers before calling services.
- This keeps controller code thin and business rules centralized.

## Architecture Diagram Summary

SupplySync is designed for maintainability and extensibility:

- APIs in Django REST Framework
- Authentication via JWT
- Background jobs through Celery
- Redis for caching and broker
- Modular app boundaries for each domain area
- Centralized exception format for consistent API behavior
