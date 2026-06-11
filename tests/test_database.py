import pytest
from models import Student, Class

def test_create_student_transaction(db_session, test_data):
    """Vérifie le CRUD de base et les relations DB."""
    student = Student(name="Transaction Test", gender="F", class_id=test_data['class'].id)
    db_session.add(student)
    db_session.commit()

    queried = Student.query.filter_by(name="Transaction Test").first()
    assert queried.current_class.name == "7è EB"

def test_delete_student(db_session, test_data):
    """Vérifie la suppression d'un élève."""
    student_id = test_data['student'].id
    student = Student.query.get(student_id)
    db_session.delete(student)
    db_session.commit()

    assert Student.query.get(student_id) is None
