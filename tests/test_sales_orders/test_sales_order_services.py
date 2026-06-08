import pytest
from apps.sales_orders.services import (
    create_sales_order,
    dispatch_sales_order,
    cancel_sales_order,
)
from apps.sales_orders.models import SalesOrderStatus
from core.exceptions import InvalidOperationException


def test_create_sales_order_reserves_inventory_on_creation(db, sample_inventory, staff_user):
    data = {
        'warehouse_id': sample_inventory.warehouse.id,
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '1234567890',
        'shipping_address': '123 Main St',
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 5}
        ]
    }

    so = create_sales_order(data, staff_user.id)    

    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_reserved == 5  
    assert sample_inventory.quantity_available == 15
    assert so.status == SalesOrderStatus.CONFIRMED


def test_create_sales_order_raises_exception_when_insufficient_stock(db, sample_inventory, staff_user):
    data = {
        'warehouse_id': sample_inventory.warehouse.id,
        'customer_name': 'John Doe',
        'customer_email': 'john@example.com',
        'customer_phone': '1234567890',
        'shipping_address': '123 Main St',
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 100}
        ]
    }

    from core.exceptions import InsufficientStockException

    with pytest.raises(InsufficientStockException):
        create_sales_order(data, staff_user.id)


def test_dispatch_sales_order_creates_outbound_transactions_for_all_items(db, sample_inventory, staff_user):
    data = {
        'warehouse_id': sample_inventory.warehouse.id,
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '1234567890',
        'shipping_address': '123 Main St',
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 5}
        ]
    }

    so = create_sales_order(data, staff_user.id)
    dispatched = dispatch_sales_order(so.id, staff_user.id)

    sample_inventory.refresh_from_db()
    assert dispatched.status == 'DISPATCHED'
    assert sample_inventory.quantity_reserved == 0
    assert sample_inventory.quantity_available == 15
    assert dispatched.items.count() == 1


def test_cancel_sales_order_releases_reserved_inventory(db, sample_inventory, staff_user):
    data = {
        'warehouse_id': sample_inventory.warehouse.id,
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '1234567890',
        'shipping_address': '123 Main St',
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 10}
        ]
    }

    so = create_sales_order(data, staff_user.id)

    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 10
    assert sample_inventory.quantity_reserved == 10

    canceled = cancel_sales_order(so.id, 'Customer changed mind')

    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 20
    assert sample_inventory.quantity_reserved == 0
    assert canceled.status == 'CANCELLED'


def test_cancel_sales_order_raises_exception_when_order_is_already_dispatched(db, sample_inventory, staff_user):
    data = {
        'warehouse_id': sample_inventory.warehouse.id,
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '1234567890',
        'shipping_address': '123 Main St',
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 5}
        ]
    }

    so = create_sales_order(data, staff_user.id)
    dispatch_sales_order(so.id, staff_user.id)

    with pytest.raises(InvalidOperationException):
        cancel_sales_order(so.id, 'Already dispatched')
