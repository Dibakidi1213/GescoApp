import pytest
from models import Attendance, Conduct, Incident

def test_record_attendance(client, test_data):
    """Vérifie l'enregistrement des présences."""
    login = client.post('/api/auth/login', json={'username': 'test_discipline', 'password': 'TestPassword123!'})
    token = login.get_json()['access_token']

    data = {
        'class_id': test_data['class'].id,
        'date': '2024-06-10',
        'attendances': [{'student_id': test_data['student'].id, 'status': 'absent'}]
    }

    resp = client.post('/api/discipline/attendance/bulk',
                      json=data,
                      headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 201
    att = Attendance.query.filter_by(student_id=test_data['student'].id).first()
    assert att.status == 'absent'

def test_record_incident(client, test_data):
    """Vérifie l'enregistrement d'un incident."""
    login = client.post('/api/auth/login', json={'username': 'test_discipline', 'password': 'TestPassword123!'})
    token = login.get_json()['access_token']

    data = {
        'student_id': test_data['student'].id,
        'category': 'Bagarre',
        'description': 'L\'élève a frappé un camarade',
        'severity': 'majeur'
    }

    resp = client.post('/api/discipline/incident',
                      json=data,
                      headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 201
    inc = Incident.query.filter_by(student_id=test_data['student'].id).first()
    assert inc.category == 'Bagarre'
