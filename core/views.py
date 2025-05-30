from django.shortcuts import render
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from core.models import User, UserFile, UserAction, GroupedAction
from .serializers import RegisterSerializer, UserFileSerializer, UserActionSerializer, GroupedActionSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utils import predict_risk, get_geo_from_ip, count_recent_actions, group_recent_actions
from django.utils.timezone import now
from rest_framework.decorators import action, api_view, permission_classes
import socket
from django.core.management import call_command
from django.db.models.functions import TruncDate
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alerts_view(request):
    now = timezone.now()
    start = now - timedelta(minutes=5)  # показывать алерты только за последние 5 минут

    # Одиночные подозрительные действия
    single_logs = UserAction.objects.filter(
        risk_level__in=['critical', 'suspicious'],
        timestamp__gte=start
    )

    # Групповые подозрительные действия
    grouped_logs = GroupedAction.objects.filter(
        risk_level__in=['critical', 'suspicious'],
        end_time__gte=start
    )

    # Сериализуем всё в один список, можно добавить тип для фронта
    result = []

    for log in single_logs:
        result.append({
            'id': f"single-{log.id}",
            'type': 'single',
            'user': log.user.username,
            'action': log.action_type,
            'file': log.file_name,
            'risk': log.risk_level,
            'time': log.timestamp,
        })

    for log in grouped_logs:
        result.append({
            'id': f"group-{log.id}",
            'type': 'group',
            'user': log.user.username,
            'action': log.action_type,
            'count': log.actions_count,
            'risk': log.risk_level,
            'start_time': log.start_time,
            'end_time': log.end_time,
        })

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def action_stats(request):
    if request.user.role != 'admin':
        return Response({'error': 'Access denied'}, status=403)

    logs = UserAction.objects.annotate(date=TruncDate('timestamp')).values('date').annotate(total=Count('id')).order_by('date')
    return Response(list(logs))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retrain_model_view(request):
    if request.user.role != 'admin':
        return Response({'error': 'Access denied'}, status=403)

    try:
        call_command('retrain_model')
        return Response({'message': 'Model retrained successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

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

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_grouped_risk_level(request, group_id):
    if request.user.role != 'admin':
        return Response({'error': 'Access denied'}, status=403)

    try:
        group = GroupedAction.objects.get(id=group_id)
        new_risk = request.data.get('risk_level')
        if new_risk not in ['normal', 'suspicious', 'critical']:
            return Response({'error': 'Invalid risk level'}, status=400)
        group.risk_level = new_risk
        group.save()
        return Response({'message': 'Group risk updated'})
    except GroupedAction.DoesNotExist:
        return Response({'error': 'Grouped log not found'}, status=404)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserFileViewSet(viewsets.ModelViewSet):
    queryset = UserFile.objects.all()
    serializer_class = UserFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFile.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self.log_action('upload', instance.filename)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.user and request.user.role != 'admin':
            return Response({'error': 'Нельзя удалить чужой файл'}, status=403)

        filename = instance.filename

        self.log_action('delete', filename)
        group_recent_actions(request.user, 'delete', minutes=5, min_count=3)

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        file_instance = self.get_object()
        self.log_action('download', file_instance.filename)

        # (Логика доступа — например, скачивать можно все файлы или только свои/доступные)
        try:
            response = FileResponse(file_instance.file.open('rb'), as_attachment=True)
            return response
        except Exception:
            raise Http404("Файл не найден или ошибка доступа")

    @action(detail=True, methods=['get'], url_path='view')
    def view_file(self, request, pk=None):
        file_instance = self.get_object()
        self.log_action('view', file_instance.filename)
        try:
            # Для просмотра можно отдавать inline, или отдавать ссылку на миниатюру (если это картинка)
            return FileResponse(file_instance.file.open('rb'), as_attachment=False)
        except Exception:
            raise Http404("Файл не найден или ошибка доступа")

    def log_action(self, action_type, filename):
        ip = self.get_client_ip()
        city, country = get_geo_from_ip(ip)
        actions_last_5min = count_recent_actions(self.request.user, action_type, minutes=5)

        if actions_last_5min >= 2:
            risk = predict_risk(action_type, actions_last_5min)
        else:
            risk = "unknown"

        UserAction.objects.create(
            user=self.request.user,
            action_type=action_type,
            file_name=filename,
            ip_address=ip,
            city=city,
            country=country,
            actions_last_5min=actions_last_5min,
            risk_level=risk,
        )
        group_recent_actions(self.request.user, action_type, minutes=5, min_count=2)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({
        "username": request.user.username,
        "role": request.user.role
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grouped_actions_list(request):
    groups = GroupedAction.objects.all().order_by('-start_time')
    serializer = GroupedActionSerializer(groups, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_stats(request):
    if request.user.role != 'admin':
        return Response({'error': 'Forbidden'}, status=403)
    stats = (
        UserAction.objects
        .annotate(date=TruncDate('timestamp'))
        .values('user__username', 'date', 'action_type')
        .annotate(count=Count('id'))
        .order_by('user__username', 'date', 'action_type')
    )
    return Response(list(stats))

