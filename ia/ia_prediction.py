import numpy as np
from sklearn.linear_model import LinearRegression
from models import Grade

def predict_final_result(student_id):
    """
    Prédit la note finale basée sur l'évolution des périodes.
    Algorithme : Régression Linéaire Simple.
    """
    history = Grade.query.filter_by(student_id=student_id).order_by(Grade.submitted_at).all()

    if len(history) < 2:
        return None # Pas assez de points pour une tendance

    # Organiser les données par temps/ordre
    X = np.array(range(len(history))).reshape(-1, 1)
    y = np.array([g.value for g in history])

    model = LinearRegression()
    model.fit(X, y)

    # Prédire le prochain point (ex: période suivante ou examen final)
    prediction = model.predict([[len(history)]])[0]

    return max(0, min(20, float(prediction)))

def predict_risk_of_failure(student_id):
    """
    Calcule la probabilité de réussite (score > 10).
    """
    predicted = predict_final_result(student_id)
    if predicted is None:
        return 0.5 # Neutre si inconnu

    # Logique simplifiée : plus la prédiction est basse, plus le risque est haut
    if predicted < 8:
        return 0.9 # Risque très élevé
    elif predicted < 10:
        return 0.6 # Risque élevé
    else:
        return 0.1 # Risque faible
