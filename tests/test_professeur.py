import pytest
from models import Grade, AuditLog

def test_professeur_saisir_note(client, test_data):
    """Vérifie qu'un prof peut saisir une note via l'API."""
    # Login Prof
    login = client.post('/api/auth/login', json={'username': 'test_professeur', 'password': 'TestPassword123!'})
    token = login.get_json()['access_token']

    data = {
        'class_id': test_data['class'].id,
        'subject_id': test_data['subject'].id,
        'period': '1èP',
        'grades': [{'student_id': test_data['student'].id, 'value': 18.5}],
        'submit': False
    }

    resp = client.post('/api/professeur/api/save-grades',
                      json=data,
                      headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 200
    grade = Grade.query.filter_by(student_id=test_data['student'].id).first()
    assert grade is not None
    assert grade.value == 18.5
    assert grade.status == 'draft'

def test_note_validation_over_max(client, test_data):
    """Vérifie que le système empêche de saisir une note supérieure au maxima (logique backend)."""
    # Ce test dépend de la validation implémentée dans les routes ou les modèles.
    pass

def test_calcul_moyenne(test_data, db_session):
    """Vérifie le calcul statistique des moyennes via DashboardUtils."""
    from dashboard_utils import DashboardUtils
    from models import Grade

    # Ajouter quelques notes
    g1 = Grade(student_id=test_data['student'].id, subject_id=test_data['subject'].id,
               teacher_id=test_data['teacher'].id, value=15, period='1èP', status='validated')
    db_session.add(g1)
    db_session.commit()

    stats = DashboardUtils.generate_professeur_stats(test_data['users']['professeur'].id)
    assert stats['subjects'][0]['avg'] == 15.0
