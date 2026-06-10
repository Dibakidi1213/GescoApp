from sklearn.cluster import KMeans
import numpy as np
from models import Incident

def cluster_student_incidents(student_id):
    """
    Clusterise les incidents d'un élève pour détecter des patterns de comportement.
    Algorithme : K-Means sur la gravité (numérique) et la fréquence.
    """
    incidents = Incident.query.filter_by(student_id=student_id).all()
    if len(incidents) < 4:
        return "Pas assez d'incidents pour une analyse de cluster."

    # Mapping gravité
    severity_map = {'mineur': 1, 'majeur': 3, 'critique': 5}
    data = []
    for inc in incidents:
        # On pourrait ajouter l'heure, le jour de la semaine, etc.
        data.append([severity_map.get(inc.severity.lower(), 1), inc.recorded_at.hour])

    data = np.array(data)

    # Détection de 2 clusters : Comportement occasionnel vs Chronique
    kmeans = KMeans(n_clusters=2, n_init=10)
    clusters = kmeans.fit_predict(data)

    # Analyse simplifiée
    if np.sum(clusters) > len(clusters) / 2:
        return "Tendance à des incidents graves en fin de journée."
    else:
        return "Incidents isolés sans pattern temporel fort."

def predict_future_risks(student_id):
    """
    Évalue le risque de futur incident basé sur l'historique récent.
    """
    recent = Incident.query.filter_by(student_id=student_id).order_by(Incident.recorded_at.desc()).limit(5).all()
    if not recent:
        return "Faible"

    count = len(recent)
    if count >= 4:
        return "Très Élevé"
    elif count >= 2:
        return "Modéré"
    return "Faible"
