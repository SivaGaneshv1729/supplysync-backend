import pytest
from datetime import date
from rest_framework.exceptions import PermissionDenied
from apps.purchase_orders.services import (
    create_purchase_order,
    submit_purchase_order,
    approve_purchase_order,
    receive_purchase_order,
    cancel_purchase_order,
)
from core.exceptions import InvalidOperationException


def test_create_purchase_order_generates_po_number_with_correct_format(db, sample_supplier, sample_warehouse, procurement_manager_user, sample_product):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 5}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)

    assert po.po_number.startswith('PO-')
    parts = po.po_number.split('-')
    assert len(parts) == 3
    assert parts[1] == date.today().strftime('%Y%m%d')
    assert parts[2].isdigit() and len(parts[2]) == 4


def test_approve_purchase_order_raises_exception_when_approver_is_same_as_creator(db, sample_supplier, sample_warehouse, procurement_manager_user, sample_product):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 5}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)
    po = submit_purchase_order(po.id)

    with pytest.raises(PermissionDenied):
        approve_purchase_order(po.id, procurement_manager_user.id)


def test_approve_purchase_order_raises_exception_when_status_is_not_pending_approval(db, sample_supplier, sample_warehouse, procurement_manager_user, warehouse_manager_user, sample_product):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 5}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)

    with pytest.raises(InvalidOperationException) as exc_info:
        approve_purchase_order(po.id, warehouse_manager_user.id)

    assert exc_info.value.default_code == 'INVALID_STATUS'


def test_receive_purchase_order_updates_inventory_for_received_items(db, sample_supplier, sample_warehouse, procurement_manager_user, admin_user, sample_product, sample_inventory):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 10}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)
    po = submit_purchase_order(po.id)
    po = approve_purchase_order(po.id, admin_user.id)

    po_item_id = po.items.first().id
    recv_data = {
        'actual_delivery_date': '2026-06-05',
        'items': [
            {'po_item_id': po_item_id, 'quantity_received': 10}
        ]
    }

    po = receive_purchase_order(po.id, recv_data, procurement_manager_user.id)
    assert po.status == 'RECEIVED'

    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 30


def test_receive_purchase_order_sets_status_to_partially_received_when_not_all_items_received(db, sample_supplier, sample_warehouse, procurement_manager_user, admin_user, sample_product):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 10}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)
    po = submit_purchase_order(po.id)
    po = approve_purchase_order(po.id, admin_user.id)

    po_item_id = po.items.first().id
    recv_data = {
        'actual_delivery_date': '2026-06-05',
        'items': [
            {'po_item_id': po_item_id, 'quantity_received': 5}
        ]
    }

    po = receive_purchase_order(po.id, recv_data, procurement_manager_user.id)
    assert po.status == 'PARTIALLY_RECEIVED'


def test_cancel_purchase_order_raises_exception_when_status_is_received(db, sample_supplier, sample_warehouse, procurement_manager_user, admin_user, sample_product):
    data = {
        'supplier_id': sample_supplier.id,
        'warehouse_id': sample_warehouse.id,
        'items': [
            {'product_id': sample_product.id, 'quantity': 5}
        ]
    }

    po = create_purchase_order(data, procurement_manager_user.id)
    po = submit_purchase_order(po.id)
    po = approve_purchase_order(po.id, admin_user.id)

    po_item_id = po.items.first().id
    recv_data = {
        'actual_delivery_date': '2026-06-05',
        'items': [
            {'po_item_id': po_item_id, 'quantity_received': 5}
        ]
    }

    po = receive_purchase_order(po.id, recv_data, procurement_manager_user.id)

    with pytest.raises(InvalidOperationException) as exc_info:
        cancel_purchase_order(po.id, 'Cannot cancel after received')

    assert exc_info.value.default_code == 'PO_CANCELLATION_NOT_ALLOWED'
