from django.core.management.base import BaseCommand
from core.models import UserAction
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

class Command(BaseCommand):
    help = "Retrain ML model using manually labeled logs"

    def handle(self, *args, **options):
        logs = UserAction.objects.all()

        if logs.count() < 5:
            self.stdout.write("Недостаточно данных для обучения.")
            return

        # Преобразуем в DataFrame
        data = pd.DataFrame(list(logs.values(
            'action_type', 'timestamp', 'session_file_count', 'risk_level'
        )))

        if data.empty:
            self.stdout.write("Нет данных для обучения.")
            return

        # Категоризация
        data['hour'] = pd.to_datetime(data['timestamp']).dt.hour
        type_map = {'upload': 0, 'download': 1, 'delete': 2, 'view': 3}
        data['action_type'] = data['action_type'].map(type_map)
        data['risk'] = data['risk_level'].astype('category')
        label_map = dict(enumerate(data['risk'].cat.categories))

        X = data[['action_type', 'hour', 'session_file_count']]
        y = data['risk'].cat.codes

        # Обучение модели
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X, y)

        # Сохраняем
        joblib.dump(model, 'ml/risk_model.joblib')
        joblib.dump(label_map, 'ml/label_map.joblib')

        self.stdout.write("Модель успешно дообучена на {} записях.".format(len(data)))
