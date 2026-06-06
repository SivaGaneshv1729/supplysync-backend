from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .validators import validate_password_strength
from .models import UserRole

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False, max_length=50)
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, validators=[validate_password_strength])
    full_name = serializers.CharField(required=True, allow_blank=False, max_length=150)
    role = serializers.ChoiceField(choices=UserRole.choices, required=True, allow_blank=False)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    new_password = serializers.CharField(required=True, allow_blank=False, write_only=True, validators=[validate_password_strength])
