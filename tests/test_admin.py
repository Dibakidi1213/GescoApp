import pytest
from models import School, AuditLog

def test_create_user_admin(client, test_data):
    """Vérifie qu'un admin peut créer une école (via la route schools)."""
    login = client.post('/api/auth/login', json={'username': 'test_admin', 'password': 'TestPassword123!'})
    token = login.get_json()['access_token']

    data = {
        'name': 'Nouvelle Ecole Admin',
        'address': '123 Rue de la Paix',
        'year_start': 2024,
        'year_end': 2025
    }

    resp = client.post('/api/admin/schools',
                      json=data,
                      headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 201
    school = School.query.filter_by(name='Nouvelle Ecole Admin').first()
    assert school is not None

def test_audit_log_tracking(client, test_data, db_session):
    """Vérifie que les actions critiques sont logguées."""
    login = client.post('/api/auth/login', json={'username': 'test_admin', 'password': 'TestPassword123!'})
    from models import AuditLog
    logs = AuditLog.query.all()
    assert len(logs) > 0
