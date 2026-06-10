import unittest
from app import create_app
from models import db, User, School, Student, Teacher, Subject, Class
from config import Config

class MobileApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Setup data
        self.school = School(name="MobileSchool")
        db.session.add(self.school)
        db.session.commit()

        self.prof = User(username='prof_mob', email='p@m.com', role='professeur', school_id=self.school.id)
        self.prof.set_password('Prof1234')
        db.session.add(self.prof)
        db.session.commit()

        # Login to get token
        resp = self.client.post('/api/auth/login', json={'username': 'prof_mob', 'password': 'Prof1234'})
        self.token = resp.get_json()['access_token']

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_subjects(self):
        """Vérifie que le prof peut lister ses matières."""
        resp = self.client.get('/api/mobile/professeur/subjects', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()
