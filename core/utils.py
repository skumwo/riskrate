import joblib
from django.utils import timezone
from datetime import datetime, timedelta
from .models import UserAction, UserFile, GroupedAction
import requests

model = joblib.load('ml/risk_model.joblib')
label_map = joblib.load('ml/label_map.joblib')

import pandas as pd

def predict_risk(action_type, actions_last_5min):
    hour = datetime.now().hour
    type_map = {'upload': 0, 'download': 1, 'delete': 2, 'view': 3}
    type_code = type_map.get(action_type, 0)

    input_df = pd.DataFrame(
        [[type_code, hour, actions_last_5min]],
        columns=["action_type", "hour", "actions_last_5min"]
    )
    prediction = model.predict(input_df)[0]
    return label_map[prediction]

def group_recent_actions(user, action_type, minutes=5, min_count=2):
    now = timezone.now()
    start = now - timedelta(minutes=minutes)

    logs = UserAction.objects.filter(
        user=user,
        action_type=action_type,
        timestamp__gte=start
    ).order_by('timestamp')

    if logs.count() < min_count:
        return None

    # Проверяем — есть ли уже активная группа, которую можно расширить?
    recent_group = GroupedAction.objects.filter(
        user=user,
        action_type=action_type,
        end_time__gte=start
    ).order_by('-end_time').first()

    if recent_group:
        # Обновляем конец периода, количество действий и связанные логи!
        recent_group.end_time = logs.last().timestamp
        recent_group.actions_count = logs.count()
        recent_group.session_file_count = UserFile.objects.filter(user=user).count()
        # ! Обновим риск для уже существующей группы:
        recent_group.risk_level = predict_risk(action_type, logs.count())
        recent_group.actions.set(logs)
        recent_group.save()
        return recent_group

    # Если нет активной — создаём новую группу
    risk = predict_risk(action_type, logs.count())  # <--- здесь вычисляем риск

    grouped = GroupedAction.objects.create(
        user=user,
        action_type=action_type,
        hour=now.hour,
        actions_count=logs.count(),
        session_file_count=UserFile.objects.filter(user=user).count(),
        start_time=logs.first().timestamp,
        end_time=logs.last().timestamp,
        risk_level=risk,  # <--- сохраняем риск в новую группу
    )
    grouped.actions.set(logs)
    grouped.save()
    return grouped

def count_recent_actions(user, action_type, minutes=5):
    time_threshold = timezone.now() - timedelta(minutes=minutes)
    return UserAction.objects.filter(
        user=user,
        action_type=action_type,
        timestamp__gte=time_threshold
    ).count()

def get_geo_from_ip(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return data.get('city'), data.get('country')
    except Exception:
        return None, None

