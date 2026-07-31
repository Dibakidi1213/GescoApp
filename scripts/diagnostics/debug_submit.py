from app import app
from models import db, User, Course

with app.app_context():
    # Get testprof
    prof = User.query.filter_by(username='testprof').first()
    print(f"Professor: {prof.username}, Role: {prof.role}, School: {prof.school_id}")
    print(f"is_professor(): {prof.is_professor()}")
    
    # Get the course
    course = Course.query.filter_by(id=5).first()
    if course:
        print(f"\nCourse ID: {course.id}")
        print(f"Course professor_id: {course.professor_id}")
        print(f"Course school_id: {course.school_id}")
        print(f"Matches prof? {course.professor_id == prof.id and course.school_id == prof.school_id}")
    else:
        print("Course not found!")
