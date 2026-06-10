import numpy as np
from scipy import stats
from models import Grade, Student

def detect_grade_anomaly(student_id, new_grade_value, subject_id):
    """
    Détecte si une nouvelle note est une anomalie statistique (Z-score).
    Algorithme : Z-score (Nombre d'écarts types par rapport à la moyenne historique).
    """
    # Récupérer l'historique des notes de l'élève pour cette matière
    history = Grade.query.filter_by(student_id=student_id, subject_id=subject_id).all()
    if len(history) < 3:
        return False, 0.0 # Pas assez de données pour conclure

    values = [g.value for g in history]
    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return False, 0.0

    z_score = abs((new_grade_value - mean) / std)

    # Un Z-score > 2.5 est généralement considéré comme une anomalie forte
    is_anomaly = z_score > 2.5

    # Cas spécifiques demandés :
    # 1. Note > 95% alors que moyenne habituelle < 70%
    if new_grade_value > 19 and mean < 14: # Sur 20
        is_anomaly = True
    # 2. Note < 10% alors que moyenne habituelle > 80%
    if new_grade_value < 2 and mean > 16:
        is_anomaly = True

    return is_anomaly, z_score

def detect_cheating_pattern(class_id, subject_id, period):
    """
    Identifie des patterns de triche potentiels (notes identiques suspectes).
    """
    grades = Grade.query.filter_by(subject_id=subject_id, period=period).all()
    if not grades:
        return []

    # Analyse de la distribution des notes
    value_counts = {}
    for g in grades:
        value_counts[g.value] = value_counts.get(g.value, 0) + 1

    anomalies = []
    for val, count in value_counts.items():
        # Si plus de 30% de la classe a exactement la même note (hors cas triviaux comme 0 ou 20)
        if count > len(grades) * 0.3 and val not in [0, 10, 20]:
            anomalies.append({'value': val, 'count': count, 'percentage': (count/len(grades))*100})

    return anomalies
