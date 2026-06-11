import pytest
from ia.ia_anomalies import detect_grade_anomaly
from ia.ia_appreciations import generate_appreciation

def test_detect_anomaly_logic(test_data):
    """Vérifie l'algorithme de détection d'anomalies."""
    # Test simple avec peu de données
    is_anomaly, score = detect_grade_anomaly(test_data['student'].id, 15, test_data['subject'].id)
    assert is_anomaly is False

def test_generate_appreciation_ia(app, test_data, db_session):
    """Vérifie la génération d'appréciations par IA."""
    with app.app_context():
        from models import Grade
        g1 = Grade(student_id=test_data['student'].id, subject_id=test_data['subject'].id,
                   teacher_id=test_data['teacher'].id, value=18, period='1èP', status='validated')
        db_session.add(g1)
        db_session.commit()

        text, level = generate_appreciation(test_data['student'].id, '1èP')
        assert "Excellent" in level or "Exceptionnel" in text
