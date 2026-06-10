from app import create_app
from models import db, School, Class, Student, Subject, User, Teacher, Grade
from datetime import date
import random

app = create_app()
with app.app_context():
    db.create_all()

    school = School.query.filter_by(name="COMPLEXE SCOLAIRE LA PERFECTION").first()
    if not school:
        school = School(
            name="COMPLEXE SCOLAIRE LA PERFECTION",
            address="Avenue de la Paix, Kinshasa",
            province="KINSHASA", ville="KINSHASA", commune="NGALIEMA", code="60123456",
            year_start=2024, year_end=2025
        )
        db.session.add(school)
        db.session.commit()

    # 1. Classe de 7ème Education de Base (CTEB)
    class_7eb = Class.query.filter_by(name="7ème EB", school_id=school.id).first()
    if not class_7eb:
        class_7eb = Class(name="7ème EB", level="7", section="EDUCATION DE BASE", school_id=school.id, capacity=40)
        db.session.add(class_7eb)
        db.session.commit()

    # Curriculum CTEB (7è / 8è)
    cteb_curriculum = [
        # Domaine des Sciences
        ("Algèbre", "DOMAINE DES SCIENCES", "Sous domaine des mathématiques", 40, 80),
        ("Arithmétique", "DOMAINE DES SCIENCES", "Sous domaine des mathématiques", 10, 20),
        ("Géométrie", "DOMAINE DES SCIENCES", "Sous domaine des mathématiques", 20, 40),
        ("Statistique", "DOMAINE DES SCIENCES", "Sous domaine des mathématiques", 10, 20),

        ("Anatomie", "DOMAINE DES SCIENCES", "Sous domaine des sciences de la vie et de la terre", 10, 20),
        ("Botanique", "DOMAINE DES SCIENCES", "Sous domaine des sciences de la vie et de la terre", 10, 20),
        ("Zoologie", "DOMAINE DES SCIENCES", "Sous domaine des sciences de la vie et de la terre", 20, 40),

        ("Sciences Physiques", "DOMAINE DES SCIENCES", "Sous domaine des sciences Physiques, Technologie et Tic", 10, 20),
        ("Technologie", "DOMAINE DES SCIENCES", "Sous domaine des sciences Physiques, Technologie et Tic", 10, 20),
        ("Techno d'Info & Com(TIC)", "DOMAINE DES SCIENCES", "Sous domaine des sciences Physiques, Technologie et Tic", 10, 20),

        # Domaine des Langues
        ("Anglais", "DOMAINE DES LANGUES", "", 30, 60),
        ("Français", "DOMAINE DES LANGUES", "", 50, 100),

        # Domaine Social
        ("Religion", "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", "", 20, 40),
        ("Education à la vie", "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", "", 20, 40),
        ("Education civique et moral", "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", "", 20, 40),
        ("Géographie", "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", "", 30, 60),
        ("Histoire", "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", "", 20, 40),

        # Arts
        ("Dessin", "DOMAINE DES ARTS", "", 20, 40),
        ("Musique", "DOMAINE DES ARTS", "", 20, 40),

        # Développement Personnel
        ("Education Physique", "DOMAINE DU DEVELOPPEMENT PERSONNEL", "", 20, 40),
    ]

    for s_name, dom, sd, m_p, m_e in cteb_curriculum:
        subj = Subject.query.filter_by(name=s_name, class_id=class_7eb.id).first()
        if not subj:
            subj = Subject(name=s_name, domain=dom, sub_domain=sd,
                           max_1p=m_p, max_2p=m_p, max_exa1=m_e,
                           max_3p=m_p, max_4p=m_p, max_exa2=m_e,
                           class_id=class_7eb.id)
            db.session.add(subj)
    db.session.commit()

    # 2. Elève et Notes
    student = Student.query.filter_by(name="MUKADI JEAN").first()
    if not student:
        student = Student(name="MUKADI JEAN", gender="M", birth_date=date(2012, 3, 4), birth_place="Kinshasa", class_id=class_7eb.id)
        db.session.add(student)
        db.session.commit()

    subjects = Subject.query.filter_by(class_id=class_7eb.id).all()
    for s in subjects:
        for p in ["1èP", "2èP", "EXA1"]:
            max_v = s.max_1p if "P" in p else s.max_exa1
            grade = Grade(student_id=student.id, subject_id=s.id, teacher_id=1, value=round(random.uniform(0.5, 0.9)*max_v, 1), period=p, status="validated")
            db.session.add(grade)

    db.session.commit()
    print("Initialisation CTEB terminée.")
