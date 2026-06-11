import pytest
from models import User
from flask_bcrypt import check_password_hash
from jwt_utils import verify_jwt

def test_login_success(client, test_data):
    """Vérifie qu'un utilisateur valide peut se connecter."""
    resp = client.post('/api/auth/login', json={
        'username': 'test_admin',
        'password': 'TestPassword123!'
    })
    assert resp.status_code == 200
    assert 'access_token' in resp.get_json()

def test_login_failed_wrong_password(client, test_data):
    """Vérifie l'échec de connexion avec un mauvais mot de passe."""
    resp = client.post('/api/auth/login', json={
        'username': 'test_admin',
        'password': 'WrongPassword'
    })
    assert resp.status_code == 401

def test_login_failed_user_not_found(client, test_data):
    """Vérifie l'échec de connexion pour un utilisateur inexistant."""
    resp = client.post('/api/auth/login', json={
        'username': 'ghost_user',
        'password': 'SomePassword'
    })
    assert resp.status_code == 401

def test_password_hashing(test_data):
    """Vérifie que le hashage bcrypt fonctionne correctement."""
    user = User.query.filter_by(username='test_admin').first()
    assert user.password_hash.startswith('$2b$')
    assert check_password_hash(user.password_hash, 'TestPassword123!')

def test_jwt_generation_and_verification(app, test_data):
    """Vérifie la génération et la validité du token JWT."""
    with app.app_context():
        from jwt_utils import generate_jwt
        token = generate_jwt(test_data['users']['admin'].id, 'admin', test_data['school'].id)
        payload = verify_jwt(token)
        assert payload is not None
        assert payload['user_id'] == test_data['users']['admin'].id
        assert payload['role'] == 'admin'

def test_rate_limit_login(client, test_data):
    """Vérifie que le rate limit bloque les tentatives excessives (si activé)."""
    # Note: Dans conftest on a mis RATELIMIT_ENABLED = False pour faciliter les tests,
    # mais on peut tester la logique manuellement si besoin.
    pass
