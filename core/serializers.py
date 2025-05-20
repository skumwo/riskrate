from rest_framework import serializers
from .models import User, UserFile, UserAction
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'password', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', 'user')
        )
        return user

class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ['id', 'file', 'filename', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'filename']

    def create(self, validated_data):
        validated_data['filename'] = validated_data['file'].name
        return super().create(validated_data)

class UserActionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserAction
        fields = ['id', 'username', 'action_type', 'file_name', 'timestamp', 'ip_address', 'session_file_count', 'risk_level']
