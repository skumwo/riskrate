import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

data = pd.DataFrame([
    {"action_type": "upload", "hour": 14, "actions_last_5min": 2, "risk": "normal"},
    {"action_type": "delete", "hour": 3, "actions_last_5min": 10, "risk": "critical"},
    {"action_type": "download", "hour": 23, "actions_last_5min": 6, "risk": "suspicious"},
    {"action_type": "view", "hour": 10, "actions_last_5min": 1, "risk": "normal"},
    {"action_type": "upload", "hour": 2, "actions_last_5min": 8, "risk": "critical"},
    {"action_type": "download", "hour": 16, "actions_last_5min": 1, "risk": "normal"},
    {"action_type": "delete", "hour": 18, "actions_last_5min": 2, "risk": "suspicious"},
    {"action_type": "delete", "hour": 3, "actions_last_5min": 8, "risk": "critical"},
    {"action_type": "upload", "hour": 2, "actions_last_5min": 7, "risk": "suspicious"},
    {"action_type": "download", "hour": 23, "actions_last_5min": 12, "risk": "critical"},
])

data['action_type'] = data['action_type'].astype('category').cat.codes
data['risk'] = data['risk'].astype('category')

X = data[['action_type', 'hour', 'actions_last_5min']]
y = data['risk'].cat.codes
label_map = dict(enumerate(data['risk'].cat.categories))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

joblib.dump(model, 'ml/risk_model.joblib')
joblib.dump(label_map, 'ml/label_map.joblib')
print("Модель обучена и сохранена.")
