from app import create_app
from models import Student

app = create_app()
with app.app_context():
    # Get students of different levels
    students = Student.query.limit(10).all()
    for s in students:
        level = s.section.level if s.section else "N/A"
        print(f"ID: {s.id}, Name: {s.last_name} {s.first_name}, Level: {level}")
