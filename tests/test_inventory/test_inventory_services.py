import pytest
from core.exceptions import InsufficientInventoryException
from apps.inventory.models import InventoryTransaction, TransactionType
from apps.inventory.services import adjust_inventory, transfer_inventory, get_low_stock_alerts
from apps.warehouses.models import Warehouse


def test_adjust_inventory_creates_transaction_record_when_inbound(db, sample_inventory, staff_user):
    payload = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': TransactionType.INBOUND,
        'quantity': 5,
        'notes': 'Inbound test'
    }

    txn = adjust_inventory(payload, staff_user.id)

    assert InventoryTransaction.objects.filter(id=txn.id).exists()
    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 25


def test_adjust_inventory_raises_exception_when_outbound_exceeds_available(db, sample_inventory, staff_user):
    payload = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': TransactionType.OUTBOUND,
        'quantity': 100,
        'notes': 'Outbound test'
    }

    with pytest.raises(InsufficientInventoryException):
        adjust_inventory(payload, staff_user.id)


def test_adjust_inventory_dispatches_celery_task_on_success(db, sample_inventory, staff_user, mocker):
    mock_task = mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')

    payload = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': TransactionType.INBOUND,
        'quantity': 5,
        'notes': 'Inbound task'
    }

    txn = adjust_inventory(payload, staff_user.id)

    mock_task.assert_called_once_with(sample_inventory.product.id, sample_inventory.warehouse.id, TransactionType.INBOUND, 5)
    assert txn.quantity == 5


def test_transfer_inventory_deducts_from_source_and_adds_to_destination(db, sample_inventory, staff_user, sample_warehouse):
    destination = Warehouse.objects.create(
        warehouse_code='WH-DEST1',
        name='Destination Warehouse',
        location='456 Destination St',
        city='Test City',
        state='Test State',
        pincode='654321',
        capacity=500
    )

    payload = {
        'product_id': sample_inventory.product.id,
        'source_warehouse_id': sample_inventory.warehouse.id,
        'destination_warehouse_id': destination.id,
        'quantity': 5,
        'notes': 'Transfer test'
    }

    result = transfer_inventory(payload, staff_user.id)

    sample_inventory.refresh_from_db()
    dest_inventory = sample_inventory.product.inventory_set.get(warehouse=destination)

    assert sample_inventory.quantity_available == 15
    assert dest_inventory.quantity_available == 5
    assert result['outbound'].transaction_type == TransactionType.OUTBOUND
    assert result['inbound'].transaction_type == TransactionType.INBOUND


def test_transfer_inventory_raises_exception_when_source_has_insufficient_stock(db, sample_inventory, staff_user):
    from apps.warehouses.models import Warehouse

    destination = Warehouse.objects.create(
        warehouse_code='WH-FAIL',
        name='Fail Warehouse',
        location='789 Fail Rd',
        city='Test City',
        state='Test State',
        pincode='999999',
        capacity=500
    )

    payload = {
        'product_id': sample_inventory.product.id,
        'source_warehouse_id': sample_inventory.warehouse.id,
        'destination_warehouse_id': destination.id,
        'quantity': 100,
        'notes': 'Transfer fail'
    }

    with pytest.raises(InsufficientInventoryException):
        transfer_inventory(payload, staff_user.id)


def test_get_low_stock_alerts_returns_products_below_reorder_level(db, sample_inventory):
    sample_inventory.quantity_available = 4
    sample_inventory.save(update_fields=['quantity_available'])

    alerts = get_low_stock_alerts()

    assert isinstance(alerts, list)
    assert alerts[0]['product_id'] == sample_inventory.product.id
    assert alerts[0]['warehouse_id'] == sample_inventory.warehouse.id
    assert alerts[0]['deficit'] == sample_inventory.product.reorder_level - sample_inventory.quantity_available
