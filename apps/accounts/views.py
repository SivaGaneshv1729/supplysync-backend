from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAuthenticated
from core.exceptions import InvalidOperationException
from core.throttles import LoginRateLimitThrottle
from .serializers import RegisterSerializer, LoginSerializer, ChangePasswordSerializer
from .services import (
    register_user,
    login_user,
    logout_user,
    change_password,
    get_login_throttle,
)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = register_user(serializer.validated_data)
        return Response(tokens, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    throttle_classes = [LoginRateLimitThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        throttle = get_login_throttle()
        if not throttle.allow_request(request, self):
            raise InvalidOperationException(detail='Too many failed login attempts.', code='TOO_MANY_LOGIN_ATTEMPTS')

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            tokens = login_user(request, email, password)
        except (InvalidOperationException, NotAuthenticated) as exc:
            throttle.increment(request, self)
            raise exc

        throttle.reset(request, self)
        return Response(tokens, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            raise InvalidOperationException(detail='Refresh token is required.', code='MISSING_TOKEN')

        logout_user(refresh_token)
        return Response(status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_password(request.user, serializer.validated_data['old_password'], serializer.validated_data['new_password'])
        return Response(status=status.HTTP_200_OK)
