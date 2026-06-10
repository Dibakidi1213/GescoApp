import os
from app import db
from models import School, AcademicYear, Section, Student

# Configuration
SCHOOL_NAME = "Ecole Test"
ACADEMIC_YEAR_NAME = "2025 - 2026"
SECTION_BASE_NAME = "Latin Philo"
LEVELS = [1, 2, 3, 4]
STUDENTS_PER_LEVEL = 10

def create_school():
    school = School.query.filter_by(name=SCHOOL_NAME).first()
    if not school:
        school = School(name=SCHOOL_NAME)
        db.session.add(school)
        db.session.commit()
    return school

def get_or_create_academic_year(school):
    year = AcademicYear.query.filter_by(name=ACADEMIC_YEAR_NAME, school_id=school.id).first()
    if not year:
        year = AcademicYear(name=ACADEMIC_YEAR_NAME, school_id=school.id, is_current=True)
        db.session.add(year)
        db.session.commit()
    return year

def create_sections(school, year):
    sections = []
    for lvl in LEVELS:
        sec = Section.query.filter_by(name=SECTION_BASE_NAME, level=lvl, school_id=school.id, academic_year_id=year.id).first()
        if not sec:
            sec = Section(
                name=SECTION_BASE_NAME,
                level=lvl,
                school_id=school.id,
                academic_year_id=year.id
            )
            db.session.add(sec)
            db.session.commit()
        sections.append(sec)
    return sections

def create_students(school, year, sections):
    for sec in sections:
        existing = Student.query.filter_by(section_id=sec.id, academic_year_id=year.id).count()
        needed = STUDENTS_PER_LEVEL - existing
        for i in range(1, needed + 1):
            student = Student(
                first_name=f"Eleve{sec.level}_{existing + i}",
                last_name="Test",
                serial_number=f"LP{sec.level}{existing + i:02d}",
                school_id=school.id,
                academic_year_id=year.id,
                section_id=sec.id,
                gender="M"  # simple placeholder
            )
            db.session.add(student)
    db.session.commit()

def main():
    # make sure the script runs from project root so app context can be loaded
    os.chdir(os.path.abspath(os.path.dirname(__file__) + "/.."))
    # initialise Flask app context
    from app import create_app
    app = create_app()
    with app.app_context():
        school = create_school()
        year = get_or_create_academic_year(school)
        sections = create_sections(school, year)
        create_students(school, year, sections)
        print("Test data created successfully.")

if __name__ == "__main__":
    main()
