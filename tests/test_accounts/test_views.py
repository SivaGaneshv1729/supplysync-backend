import pytest
from rest_framework import status


def test_register_returns_201_with_valid_request(api_client):
    payload = {
        "username": "newuser",
        "email": "newuser@supplysync.com",
        "password": "Password123!",
        "full_name": "New User",
        "role": "STAFF"
    }

    response = api_client.post('/api/v1/auth/register/', payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['email'] == payload['email']
    assert response.data['username'] == payload['username']
    assert response.data['role'] == payload['role']
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data


def test_register_returns_409_when_email_already_exists(api_client, admin_user):
    payload = {
        "username": "adminduplicate",
        "email": admin_user.email,
        "password": "Password123!",
        "full_name": "Admin Duplicate",
        "role": "STAFF"
    }

    response = api_client.post('/api/v1/auth/register/', payload, format='json')

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data['error_code'] in ['DUPLICATE_RESOURCE', 'EMAIL_ALREADY_EXISTS']


def test_login_returns_200_with_valid_credentials(api_client, staff_user):
    payload = {
        "email": staff_user.email,
        "password": "Password123!"
    }

    response = api_client.post('/api/v1/auth/login/', payload, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data
    assert response.data['user_id'] == staff_user.id
    assert response.data['role'] == staff_user.role


def test_login_returns_401_with_invalid_credentials(api_client, staff_user):
    payload = {
        "email": staff_user.email,
        "password": "WrongPassword1!"
    }

    response = api_client.post('/api/v1/auth/login/', payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error_code'] == 'NOT_AUTHENTICATED'


def test_refresh_token_returns_200_with_valid_refresh_token(api_client, staff_user):
    login_payload = {
        "email": staff_user.email,
        "password": "Password123!"
    }

    login_response = api_client.post('/api/v1/auth/login/', login_payload, format='json')
    refresh_token = login_response.data['refresh_token']

    response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': refresh_token}, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
