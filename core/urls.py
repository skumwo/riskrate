from django.urls import path
from .views import RegisterView, UserFileViewSet, UserActionListView, update_risk_level, retrain_model_view, action_stats, alerts_view, current_user, grouped_actions_list, update_grouped_risk_level, user_activity_stats
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('logs/', UserActionListView.as_view(), name='user-logs'),
    path('logs/<int:log_id>/update-risk/', update_risk_level),
    path('ml/retrain/', retrain_model_view),
    path('logs/stats/', action_stats),
    path('logs/alerts/', alerts_view),
    path('logs/user-activity/', user_activity_stats),
    path('me/', current_user),
    path('grouped-actions/', grouped_actions_list),
    path('grouped-actions/<int:group_id>/update-risk/', update_grouped_risk_level),


]

router = DefaultRouter()
router.register(r'files', UserFileViewSet, basename='file')
urlpatterns += router.urls

