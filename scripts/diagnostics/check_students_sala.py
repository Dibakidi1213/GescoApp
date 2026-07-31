from app import app, db
from models import School, Student, Section

with app.app_context():
    s = School.query.filter(School.name.like('%SALA SAMBILA%')).first()
    if not s:
        print("School not found")
    else:
        print(f"School: {s.name}")
        students = Student.query.filter_by(school_id=s.id).all()
        print(f"Total students: {len(students)}")
        
        # Identify legitimate students vs test students
        students_to_delete = []
        for st in students:
            section_name = st.section.name if st.section else "None"
            print(f"ID: {st.id}, Name: {st.first_name} {st.last_name}, Class: {section_name}")
            
            # If section is None, it's likely a test student to delete
            if not st.section:
                students_to_delete.append(st)
                
        print(f"Found {len(students_to_delete)} students without a section to delete.")
        
        for st in students_to_delete:
            db.session.delete(st)
            
        db.session.commit()
        print("Deleted students without section.")
