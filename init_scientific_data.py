from app import create_app
from models import db, School, Class, Student, Subject, User, Teacher, Grade
from datetime import date
import random

app = create_app()
with app.app_context():
    db.create_all()

    # 1. École
    school = School.query.filter_by(name="INSTITUT SCIENTIFIQUE DE KINSHASA").first()
    if not school:
        school = School(
            name="INSTITUT SCIENTIFIQUE DE KINSHASA",
            address="Avenue de la Science, Gombe",
            province="KINSHASA",
            ville="KINSHASA",
            commune="GOMBE",
            code="60412345",
            year_start=2024,
            year_end=2025
        )
        db.session.add(school)
        db.session.commit()

    # 2. Classe Scientifique
    class_sci = Class.query.filter_by(name="6ème Math-Physique", school_id=school.id).first()
    if not class_sci:
        class_sci = Class(
            name="6ème Math-Physique",
            level="6",
            section="SCIENCES",
            school_id=school.id,
            capacity=40
        )
        db.session.add(class_sci)
        db.session.commit()

    # 3. Rubriques au programme Scientifique RDC
    # Groupes de maxima pour le bulletin
    program = [
        # Maxima 10
        ("Religion", "MAX_10", 10, 20),
        ("Education à la Citoyenneté", "MAX_10", 10, 20),
        ("TICE (Informatique)", "MAX_10", 10, 20),
        ("Education à la Vie", "MAX_10", 10, 20),

        # Maxima 20
        ("Chimie", "MAX_20", 20, 40),
        ("Biologie / Microbiologie", "MAX_20", 20, 40),
        ("Géographie", "MAX_20", 20, 40),
        ("Histoire", "MAX_20", 20, 40),
        ("Philosophie", "MAX_20", 20, 40),
        ("Anglais", "MAX_20", 20, 40),

        # Maxima 40
        ("Physique", "MAX_40", 40, 80),

        # Maxima 50
        ("Mathématiques", "MAX_50", 50, 100),
        ("Français", "MAX_50", 50, 100)
    ]

    subjects = []
    for s_name, domain, m_p, m_e in program:
        subj = Subject.query.filter_by(name=s_name, class_id=class_sci.id).first()
        if not subj:
            subj = Subject(
                name=s_name,
                domain=domain,
                max_1p=m_p, max_2p=m_p, max_exa1=m_e,
                max_3p=m_p, max_4p=m_p, max_exa2=m_e,
                class_id=class_sci.id
            )
            db.session.add(subj)
        subjects.append(subj)
    db.session.commit()

    # 4. Elève
    student = Student.query.filter_by(name="KABAMBA DIEUDONNE").first()
    if not student:
        student = Student(
            name="KABAMBA DIEUDONNE",
            gender="M",
            birth_date=date(2007, 10, 12),
            birth_place="Kinshasa",
            class_id=class_sci.id,
            permanent_id="8901234"
        )
        db.session.add(student)
        db.session.commit()

    # 5. Notes
    for subj in subjects:
        # On met des notes réalistes
        for p in ["1èP", "2èP", "EXA1"]:
            max_val = subj.max_1p if "P" in p else subj.max_exa1
            val = round(random.uniform(0.5, 0.9) * max_val, 1)
            grade = Grade(student_id=student.id, subject_id=subj.id, teacher_id=1, value=val, period=p, status="validated")
            db.session.add(grade)

    db.session.commit()
    print("Initialisation du programme Scientifique terminée.")
