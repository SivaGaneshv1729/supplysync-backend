from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from core.exceptions import InvalidOperationException, DuplicateResourceException
from .models import User


def _build_token_response(user, is_login=False):
    refresh = RefreshToken.for_user(user)
    response = {
        "username": user.username,
        "role": user.role,
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }
    if is_login:
        response["user_id"] = user.id
    else:
        response["id"] = user.id
        response["email"] = user.email
        response["full_name"] = user.full_name
    return response


def register_user(data: dict):
    email = data['email']
    if User.objects.filter(email=email).exists():
        raise DuplicateResourceException(detail='Email already exists.', code='EMAIL_ALREADY_EXISTS')

    user = User.objects.create_user(
        email=email,
        password=data['password'],
        username=data['username'],
        full_name=data['full_name'],
        role=data['role'],
    )
    return user, _build_token_response(user, is_login=False)


def login_user(request, email: str, password: str):
    user = authenticate(request, email=email, password=password)
    if user is None:
        raise NotAuthenticated(detail='Invalid credentials.')

    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    return _build_token_response(user, is_login=True)


def logout_user(refresh_token: str):
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        raise InvalidOperationException(detail='Invalid or expired refresh token.', code='INVALID_TOKEN')


def change_password(user: User, old_password: str, new_password: str):
    if not user.check_password(old_password):
        raise InvalidOperationException(detail='Incorrect old password.', code='INCORRECT_PASSWORD')

    user.set_password(new_password)
    user.save(update_fields=['password'])


def get_login_throttle():
    from core.throttles import LoginRateLimitThrottle
    return LoginRateLimitThrottle()
