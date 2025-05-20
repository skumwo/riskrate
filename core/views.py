from django.shortcuts import render
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from .models import User, UserFile, UserAction
from .serializers import RegisterSerializer, UserFileSerializer, UserActionSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utils import predict_risk
from django.utils.timezone import now
from rest_framework.decorators import action, api_view, permission_classes
import socket
from django.db.models import Q


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_risk_level(request, log_id):
    if request.user.role != 'admin':
        return Response({'error': 'Access denied'}, status=403)

    try:
        log = UserAction.objects.get(id=log_id)
        new_risk = request.data.get('risk_level')
        if new_risk not in ['normal', 'suspicious', 'critical']:
            return Response({'error': 'Invalid risk level'}, status=400)
        log.risk_level = new_risk
        log.save()
        return Response({'message': 'Risk updated'})
    except UserAction.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserFileViewSet(viewsets.ModelViewSet):
    queryset = UserFile.objects.all()
    serializer_class = UserFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserFile.objects.all()
        return UserFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self.log_action('upload', instance.filename)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        filename = instance.filename
        self.log_action('delete', filename)
        return super().destroy(request, *args, **kwargs)

    def log_action(self, action_type, filename):
        ip = self.get_client_ip()
        count = UserFile.objects.filter(user=self.request.user).count()
        risk = predict_risk(action_type, count)

        UserAction.objects.create(
            user=self.request.user,
            action_type=action_type,
            file_name=filename,
            ip_address=ip,
            session_file_count=count,
            risk_level=risk,
        )

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class UserActionListView(generics.ListAPIView):
    serializer_class = UserActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return UserAction.objects.all().order_by('-timestamp')
        else:
            return UserAction.objects.filter(user=user).order_by('-timestamp')
