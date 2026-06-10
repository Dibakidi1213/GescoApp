from app import app, db
from models import Student

with app.app_context():
    # Get the first 5 students
    students = Student.query.limit(5).all()
    for s in students:
        level = s.section.level if s.section else "N/A"
        print(f"ID: {s.id}, Name: {s.last_name} {s.first_name}, Level: {level}")
