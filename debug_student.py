from app import app
from models import Student, Section

with app.app_context():
    student = Student.query.get(1)
    if student:
        level_str = str(student.section.level)
        name_lower = student.section.name.lower()
        print(f'Student ID 1 section: {student.section.name}')
        print(f'Section level: {student.section.level}')
        print(f'Level starts with 4: {level_str.startswith("4")}')
        print(f'Name lower: {name_lower}')
        print(f'Has scien: {"scien" in name_lower}')
    else:
        print('No student with ID 1')
