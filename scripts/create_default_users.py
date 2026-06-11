from app import create_app
from models import db, User, School
import os

app = create_app()
with app.app_context():
    # S'assurer que l'école existe
    school = School.query.first()
    if not school:
        school = School(name="COMPLEXE SCOLAIRE LA PERFECTION", year_start=2024, year_end=2025)
        db.session.add(school)
        db.session.commit()
        print(f"École créée : {school.name}")

    # Liste des comptes à créer
    default_users = [
        ("admin", "admin@jnc.com", "admin", "Admin123!"),
        ("secretaire", "secretaire@jnc.com", "secretaire", "Secretaire123!"),
        ("professeur", "prof@jnc.com", "professeur", "Prof123!"),
        ("discipline", "discipline@jnc.com", "discipline", "Discipline123!")
    ]

    for username, email, role, password in default_users:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                role=role,
                school_id=school.id
            )
            user.set_password(password)
            db.session.add(user)
            print(f"Utilisateur créé : {username} ({role})")
        else:
            print(f"Utilisateur existe déjà : {username}")

    db.session.commit()
    print("\nIdentifiants par défaut :")
    for username, email, role, password in default_users:
        print(f"- {role.capitalize()} : {username} / {password}")
