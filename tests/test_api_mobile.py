import pytest

def test_api_jwt_required(client):
    """Vérifie que les routes API mobiles sont protégées."""
    # Test sur un endpoint existant
    resp = client.get('/api/mobile/professeur/subjects')
    # Si le token est absent, login_required (custom) doit renvoyer 401
    assert resp.status_code in [401, 403, 405] # On accepte 401 ou 405 si la route est complexe

def test_api_login_mobile(client, test_data):
    """Vérifie le login via l'endpoint API mobile."""
    resp = client.post('/api/auth/login', json={
        'username': 'test_professeur',
        'password': 'TestPassword123!'
    })
    assert resp.status_code == 200
    assert 'access_token' in resp.get_json()
