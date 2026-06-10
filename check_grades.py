from app import app
from models import db, Grade

with app.app_context():
    grades = Grade.query.filter_by(course_id=5, period='1èP').all()
    print(f"=== Grades for Course 5, Period 1èP ===")
    for grade in grades:
        print(f"Student {grade.student_id}: value={grade.value}, submitted={grade.submitted}, submitted_at={grade.submitted_at}, submitted_by={grade.submitted_by}")
