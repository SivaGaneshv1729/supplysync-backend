import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.warehouses.models import Warehouse
from apps.categories.models import Category
from apps.products.models import Product
from apps.inventory.models import Inventory
from apps.suppliers.models import Supplier


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@supplysync.com",
        username="admin",
        password="Password123!",
        full_name="Admin User",
        role="ADMIN"
    )


@pytest.fixture
def warehouse_manager_user(db):
    return User.objects.create_user(
        email="wm@supplysync.com",
        username="warehouse_manager",
        password="Password123!",
        full_name="Warehouse Manager",
        role="WAREHOUSE_MANAGER"
    )


@pytest.fixture
def procurement_manager_user(db):
    return User.objects.create_user(
        email="pm@supplysync.com",
        username="procurement_manager",
        password="Password123!",
        full_name="Procurement Manager",
        role="PROCUREMENT_MANAGER"
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="staff@supplysync.com",
        username="staff",
        password="Password123!",
        full_name="Staff User",
        role="STAFF"
    )


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_wm_client(api_client, warehouse_manager_user):
    api_client.force_authenticate(user=warehouse_manager_user)
    return api_client


@pytest.fixture
def authenticated_pm_client(api_client, procurement_manager_user):
    api_client.force_authenticate(user=procurement_manager_user)
    return api_client


@pytest.fixture
def authenticated_staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def sample_warehouse(db):
    return Warehouse.objects.create(
        warehouse_code="WH-TEST",
        name="Test Warehouse",
        location="123 Test St",
        city="Test City",
        state="Test State",
        pincode="123456",
        capacity=1000
    )


@pytest.fixture
def sample_category(db):
    return Category.objects.create(
        category_code="CAT-TEST",
        name="Test Category"
    )


@pytest.fixture
def sample_product(db, sample_category):
    return Product.objects.create(
        sku="SKU-CAT-TEST-12345678",
        name="Test Product",
        category=sample_category,
        unit_price=10.00,
        unit_of_measure="pcs",
        reorder_level=5
    )


@pytest.fixture
def sample_supplier(db):
    return Supplier.objects.create(
        supplier_code="SUP-TEST",
        name="Test Supplier",
        contact_person="Supplier Contact",
        email="supplier@test.com",
        phone="1234567890",
        address="123 Supplier Lane",
        city="Test City",
        state="Test State",
        pincode="123456",
        gstin="GSTIN12345",
        is_active=True
    )


@pytest.fixture
def sample_inventory(db, sample_product, sample_warehouse):
    return Inventory.objects.create(
        product=sample_product,
        warehouse=sample_warehouse,
        quantity_available=20,
        quantity_reserved=0,
        quantity_damaged=0
    )
