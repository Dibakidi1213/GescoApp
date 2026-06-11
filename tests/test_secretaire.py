import pytest
from models import Grade, Bulletin

def test_validation_notes(client, test_data, db_session):
    """Vérifie qu'un secrétaire peut valider des notes."""
    # Créer une note soumise
    grade = Grade(student_id=test_data['student'].id, subject_id=test_data['subject'].id,
                  teacher_id=test_data['teacher'].id, value=14, period='1èP', status='submitted')
    db_session.add(grade)
    db_session.commit()

    login = client.post('/api/auth/login', json={'username': 'test_secretaire', 'password': 'TestPassword123!'})
    token = login.get_json()['access_token']

    resp = client.post('/api/secretaire/validate-grades',
                      json={'grade_ids': [grade.id]},
                      headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 200
    db_session.refresh(grade)
    assert grade.status == 'validated'

def test_generer_bulletin_logic(test_data, db_session):
    """Vérifie la logique de génération du bulletin (PDF mocké ou structure)."""
    from pdf_generator import generate_bulletin_pdf
    import os

    # On mock l'output path pour éviter l'écriture réelle si possible
    path = "tests/test_bulletin.pdf"
    result = generate_bulletin_pdf(test_data['student'].id, output_path=path)

    assert result is True
    assert os.path.exists(path)
    if os.path.exists(path): os.remove(path)
