import joblib
from datetime import datetime

model = joblib.load('ml/risk_model.joblib')
label_map = joblib.load('ml/label_map.joblib')

def predict_risk(action_type, session_file_count):
    hour = datetime.now().hour
    type_map = {'upload': 0, 'download': 1, 'delete': 2, 'view': 3}
    type_code = type_map.get(action_type, 0)

    input_data = [[type_code, hour, session_file_count]]
    prediction = model.predict(input_data)[0]
    return label_map[prediction]
