 de from app import app, db
from models import Student, Section, School

with app.app_context():
    school = School.query.first()
    if not school:
        print('Aucune école trouvée')
    else:
        # Get old section
        old_section = Section.query.filter_by(name='LATIN PHILO', level='3ème').first()
        if old_section:
            students = Student.query.filter_by(section_id=old_section.id).all()
            print(f'Trouvé {len(students)} élèves')
            
            # Create new sections FIRST
            section_a = Section(school_id=school.id, name='LATIN PHILO', level='3ème', class_name='A')
            section_b = Section(school_id=school.id, name='LATIN PHILO', level='3ème', class_name='B')
            db.session.add(section_a)
            db.session.add(section_b)
            db.session.commit()
            
            # NOW assign students
            for i, student in enumerate(students):
                if i < 3:
                    student.section_id = section_a.id
                    print(f'  {student.first_name} {student.last_name} -> Classe A')
                else:
                    student.section_id = section_b.id
                    print(f'  {student.first_name} {student.last_name} -> Classe B')
            
            db.session.commit()
            
            # NOW delete old section
            db.session.delete(old_section)
            db.session.commit()
            print('✓ Sections créées et élèves distribués')
