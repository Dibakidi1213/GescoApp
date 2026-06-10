import unittest
import time
from app import create_app
from models import db, User, School
from config import Config
from jwt_utils import verify_jwt

class SecurityTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = True # Activer pour le test

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SecurityTestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Setup initial data
        self.school = School(name="SecSchool")
        db.session.add(self.school)
        db.session.commit()

        self.admin = User(username='admin', email='admin@test.com', role='admin', school_id=self.school.id)
        self.admin.set_password('Admin1234')

        self.prof = User(username='prof', email='prof@test.com', role='professeur', school_id=self.school.id)
        self.prof.set_password('Prof1234')

        db.session.add_all([self.admin, self.prof])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_complexity(self):
        """Vérifie que la complexité est appliquée (via la route change-password par exemple)."""
        from auth import validate_password_complexity

        valid, _ = validate_password_complexity('short')
        self.assertFalse(valid)

        valid, _ = validate_password_complexity('NoDigits')
        self.assertFalse(valid)

        valid, _ = validate_password_complexity('Valid123')
        self.assertTrue(valid)

    def test_jwt_generation_and_verification(self):
        """Vérifie le cycle de vie du JWT."""
        with self.app.test_request_context():
            from jwt_utils import generate_jwt
            token = generate_jwt(self.admin.id, 'admin', self.school.id)
            payload = verify_jwt(token)
            self.assertIsNotNone(payload)
            self.assertEqual(payload['user_id'], self.admin.id)
            self.assertEqual(payload['role'], 'admin')

    def test_rbac_admin_route(self):
        """Vérifie que seul l'admin accède aux stats admin."""
        # Login Prof
        resp = self.client.post('/api/auth/login', json={'username': 'prof', 'password': 'Prof1234'})
        token = resp.get_json()['access_token']

        # Essai accès route admin avec token prof
        resp = self.client.get('/api/admin/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(resp.status_code, 403)

    def test_rate_limiting(self):
        """Vérifie le rate limiting sur le login."""
        for _ in range(6):
            resp = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})

        # Le 6ème devrait être bloqué par Flask-Limiter ou la logique brute force
        # Flask-Limiter renvoie 429
        self.assertEqual(resp.status_code, 429)

if __name__ == '__main__':
    unittest.main()
