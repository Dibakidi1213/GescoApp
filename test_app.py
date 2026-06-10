import unittest
from app import create_app
from models import db, User, School
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SchoolPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_database_initialization(self):
        """Vérifie que les tables sont créées."""
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = ['users', 'schools', 'classes', 'students', 'subjects', 'teachers', 'grades', 'attendance', 'conduct', 'incidents', 'bulletins', 'audit_logs']
        for table in expected_tables:
            self.assertIn(table, tables)

    def test_user_registration_and_login(self):
        """Vérifie l'enregistrement et la connexion."""
        # Création d'une école d'abord
        school = School(name="Test School")
        db.session.add(school)
        db.session.commit()

        # Comme register() est maintenant protégé, on crée le premier admin manuellement
        admin = User(username='superadmin', email='super@test.com', role='admin', school_id=school.id)
        admin.set_password('Admin1234')
        db.session.add(admin)
        db.session.commit()

        # Login SuperAdmin pour obtenir un token
        resp = self.client.post('/api/auth/login', json={'username': 'superadmin', 'password': 'Admin1234'})
        token = resp.get_json()['access_token']

        # Enregistrement d'un nouvel utilisateur via API avec le token
        resp = self.client.post('/api/auth/register',
            json={
                'username': 'admin_test',
                'email': 'admin2@test.com',
                'password': 'Password123',
                'role': 'admin',
                'school_id': school.id
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 201)

        # Login du nouvel utilisateur
        resp = self.client.post('/api/auth/login', json={
            'username': 'admin_test',
            'password': 'Password123'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('access_token', data)
        self.assertEqual(data['role'], 'admin')

if __name__ == '__main__':
    unittest.main()
