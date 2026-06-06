from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    parent_category_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'category_code', 'name', 'description', 'parent_category_id', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'category_code': {'required': False},
            'name': {'required': True, 'allow_blank': False},
        }

class CategoryTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    category_code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    
    def get_fields(self):
        fields = super().get_fields()
        fields['children'] = CategoryTreeSerializer(many=True)
        return fields
