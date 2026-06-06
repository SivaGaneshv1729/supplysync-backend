from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .validators import validate_password_strength
from .models import UserRole

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password_strength])

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'full_name', 'role']
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'full_name': {'required': True, 'allow_blank': False},
            'role': {'required': True, 'allow_null': False, 'allow_blank': False},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            role=validated_data['role']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    new_password = serializers.CharField(required=True, allow_blank=False, write_only=True, validators=[validate_password_strength])
