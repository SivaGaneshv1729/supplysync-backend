import pytest
from rest_framework import status


def test_adjust_inventory_returns_200_for_authorized_user(authenticated_staff_client, sample_inventory):
    payload = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'INBOUND',
        'quantity': 5,
        'notes': 'authorized adjust'
    }

    response = authenticated_staff_client.post('/api/v1/inventory/adjust/', payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['quantity'] == 5


def test_adjust_inventory_returns_403_for_unauthorized_role(authenticated_pm_client, sample_inventory):
    payload = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'INBOUND',
        'quantity': 5,
        'notes': 'unauthorized adjust'
    }

    response = authenticated_pm_client.post('/api/v1/inventory/adjust/', payload, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_low_stock_alerts_returns_200_with_list(authenticated_wm_client, sample_inventory):
    sample_inventory.quantity_available = 4
    sample_inventory.save(update_fields=['quantity_available'])

    response = authenticated_wm_client.get('/api/v1/inventory/low-stock/')

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) >= 1
    assert response.data[0]['product_id'] == sample_inventory.product.id


def test_transfer_inventory_returns_200_with_valid_request(authenticated_wm_client, sample_inventory):
    from apps.warehouses.models import Warehouse

    destination = Warehouse.objects.create(
        warehouse_code='WH-TRANSFER',
        name='Transfer Warehouse',
        location='456 Transfer Ave',
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
        'notes': 'transfer test'
    }

    response = authenticated_wm_client.post('/api/v1/inventory/transfer/', payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert 'outbound' in response.data and 'inbound' in response.data
    assert response.data['outbound']['quantity'] == 5
    assert response.data['inbound']['quantity'] == 5
