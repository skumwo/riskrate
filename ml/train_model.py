import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Пример данных
data = pd.DataFrame([
    {"action_type": "upload", "hour": 14, "files_count": 1, "risk": "normal"},
    {"action_type": "delete", "hour": 3, "files_count": 20, "risk": "critical"},
    {"action_type": "download", "hour": 23, "files_count": 5, "risk": "suspicious"},
    {"action_type": "view", "hour": 10, "files_count": 2, "risk": "normal"},
    {"action_type": "upload", "hour": 2, "files_count": 15, "risk": "critical"},
    {"action_type": "download", "hour": 16, "files_count": 1, "risk": "normal"},
    {"action_type": "delete", "hour": 18, "files_count": 3, "risk": "suspicious"},
    {"action_type": "delete", "hour": 3, "files_count": 1, "risk": "critical"},
    {"action_type": "upload", "hour": 2, "files_count": 20, "risk": "suspicious"},
    {"action_type": "download", "hour": 23, "files_count": 50, "risk": "critical"},

])

# Преобразуем категориальные признаки
data['action_type'] = data['action_type'].astype('category').cat.codes
data['risk'] = data['risk'].astype('category')

X = data[['action_type', 'hour', 'files_count']]
y = data['risk'].cat.codes
label_map = dict(enumerate(data['risk'].cat.categories))

# Обучение модели
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Сохраняем модель и словарь меток
joblib.dump(model, 'ml/risk_model.joblib')
joblib.dump(label_map, 'ml/label_map.joblib')
print("Модель обучена и сохранена.")
