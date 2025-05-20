from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f"{self.username} ({self.role})"

class UserAction(models.Model):
    ACTION_TYPES = (
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('view', 'View'),
        ('delete', 'Delete'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    file_name = models.CharField(max_length=255)
    session_file_count = models.IntegerField(default=1)
    risk_level = models.CharField(max_length=20, default='normal')  # normal/suspicious/critical

    def __str__(self):
        return f"{self.user.username} {self.action_type} at {self.timestamp}"

class UserFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='user_files/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.user.username})"
