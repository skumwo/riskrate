from rest_framework import serializers
from .models import User, UserFile, UserAction, GroupedAction
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
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserFile
        fields = ['id', 'file', 'filename', 'uploaded_at', 'user']
        read_only_fields = ['id', 'uploaded_at', 'filename', 'user']

    def get_user(self, obj):
        return {"username": obj.user.username}

    def create(self, validated_data):
        validated_data['filename'] = validated_data['file'].name
        return super().create(validated_data)

class UserActionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = UserAction
        fields = [
            'id', 'username', 'action_type', 'file_name',
            'timestamp', 'ip_address', 'city', 'country',
            'actions_last_5min', 'risk_level'
        ]

class GroupedActionSerializer(serializers.ModelSerializer):
    actions = UserActionSerializer(many=True, read_only=True)

    class Meta:
        model = GroupedAction
        fields = [
            'id', 'user', 'action_type', 'hour', 'actions_count',
            'session_file_count', 'start_time', 'end_time',
            'risk_level', 'actions'
        ]
