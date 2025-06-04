from django.core.management.base import BaseCommand
from core.models import UserAction, GroupedAction
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

class Command(BaseCommand):
    help = "Retrain ML model on only MASSIVE (mass-action) logs, ignoring single events."

    def handle(self, *args, **options):
        # --- Собираем UserAction ---
        logs = UserAction.objects.exclude(risk_level__isnull=True).exclude(risk_level="unknown")
        data = pd.DataFrame(list(logs.values(
            'action_type', 'timestamp', 'actions_last_5min', 'risk_level'
        )))

        # --- Добавляем GroupedAction ---
        groups = GroupedAction.objects.exclude(risk_level="unknown")
        groups_data = pd.DataFrame(list(groups.values(
            'action_type', 'start_time', 'actions_count', 'risk_level'
        )))
        if not groups_data.empty:
            groups_data = groups_data.rename(columns={
                'start_time': 'timestamp',
                'actions_count': 'actions_last_5min',
            })
            data = pd.concat([data, groups_data], ignore_index=True)

        # --- Фильтрация только массовых кейсов ---
        min_mass_action = 3  
        filtered = data[data['actions_last_5min'] >= min_mass_action].copy()

        if filtered.empty or len(filtered) < 5:
            self.stdout.write("Недостаточно массовых данных для обучения.")
            return

        filtered['hour'] = pd.to_datetime(filtered['timestamp']).dt.hour
        type_map = {'upload': 0, 'download': 1, 'delete': 2, 'view': 3}
        filtered['action_type'] = filtered['action_type'].map(type_map)
        filtered['risk'] = filtered['risk_level'].astype('category')
        label_map = dict(enumerate(filtered['risk'].cat.categories))

        # --- Аналитика: покажи сколько массовых suspicious/critical ---
        self.stdout.write(str(filtered.groupby(['action_type', 'actions_last_5min', 'risk']).size()))

        X = filtered[['action_type', 'hour', 'actions_last_5min']]
        y = filtered['risk'].cat.codes

        model = RandomForestClassifier(n_estimators=100)
        model.fit(X, y)

        joblib.dump(model, 'ml/risk_model.joblib')
        joblib.dump(label_map, 'ml/label_map.joblib')

        self.stdout.write(f"Модель обучена только на массовых действиях (actions_last_5min >= {min_mass_action}) — {len(filtered)} записей.")
