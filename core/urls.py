from django.urls import path
from .views import RegisterView, UserFileViewSet, UserActionListView, update_risk_level
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('logs/', UserActionListView.as_view(), name='user-logs'),
    path('logs/<int:log_id>/update-risk/', update_risk_level),
]

router = DefaultRouter()
router.register('files', UserFileViewSet, basename='userfile')
urlpatterns += router.urls