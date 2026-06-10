#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour initialiser et lancer GescoApp."""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import AcademicYear, BulletinConfig, School, User, slugify


def _ensure_school_columns():
    """Ajoute les colonnes manquantes à la table schools avant toute requête."""
    inspector = inspect(db.engine)

    if 'schools' not in inspector.get_table_names():
        return

    columns = [column['name'] for column in inspector.get_columns('schools')]

    if 'slogan' not in columns:
        print('Ajout de la colonne schools.slogan...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN slogan VARCHAR(255) NULL'))

    if 'study_prefect_name' not in columns:
        print('Ajout de la colonne schools.study_prefect_name...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN study_prefect_name VARCHAR(120) NULL'))

    if 'ministry' not in columns:
        print('Ajout de la colonne schools.ministry...')
        with db.engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE schools ADD COLUMN ministry VARCHAR(255) NULL DEFAULT "
                    "'MINISTERE DE L''ENSEIGNEMENT PRIMAIRE, SECONDAIRE ET TECHNIQUE'"
                )
            )

    if 'slug' not in columns:
        print('Ajout de la colonne schools.slug...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN slug VARCHAR(120) NULL'))

    if 'province' not in columns:
        print('Ajout de la colonne schools.province...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN province VARCHAR(120) NULL'))

    if 'city' not in columns:
        print('Ajout de la colonne schools.city...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN city VARCHAR(120) NULL'))

    if 'commune' not in columns:
        print('Ajout de la colonne schools.commune...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN commune VARCHAR(120) NULL'))

    if 'bulletin_school_name' not in columns:
        print('Ajout de la colonne schools.bulletin_school_name...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN bulletin_school_name VARCHAR(255) NULL'))

    if 'school_code' not in columns:
        print('Ajout de la colonne schools.school_code...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE schools ADD COLUMN school_code VARCHAR(50) NULL'))

    indexes = [idx['name'] for idx in inspector.get_indexes('schools')]
    if 'idx_schools_slug' not in indexes:
        print("Ajout de l'index unique schools.slug...")
        with db.engine.begin() as conn:
            conn.execute(text('CREATE UNIQUE INDEX idx_schools_slug ON schools (slug)'))


def _populate_school_slugs():
    """Remplit les slugs manquants pour les écoles existantes."""
    for school in School.query.filter((School.slug == None) | (School.slug == '')).all():
        candidate = slugify(school.name)
        base = candidate
        suffix = 1
        while School.query.filter(School.slug == candidate).filter(School.id != school.id).first():
            candidate = f"{base}-{suffix}"
            suffix += 1
        school.slug = candidate
        db.session.add(school)
    db.session.commit()


def _ensure_bulletin_config_columns():
    """Ajoute les colonnes manquantes à la table bulletin_configs avant toute requête."""
    inspector = inspect(db.engine)

    if 'bulletin_configs' not in inspector.get_table_names():
        return

    columns = [column['name'] for column in inspector.get_columns('bulletin_configs')]

    if 'academic_year' not in columns:
        print('Ajout de la colonne bulletin_configs.academic_year...')
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN academic_year VARCHAR(30) NULL'))

        active_year = AcademicYear.query.filter_by(is_active=True).first()
        active_year_name = active_year.name if active_year else '2025 - 2026'

        BulletinConfig.query.filter(BulletinConfig.academic_year == None).update(
            {BulletinConfig.academic_year: active_year_name}
        )
        db.session.commit()


def init_db():
    """Initialise la base de données de façon idempotente."""
    print('Initialisation de la base de données...')
    with app.app_context():
        try:
            db.create_all()
            print('Tables créées/vérifiées')

            _ensure_school_columns()
            _ensure_bulletin_config_columns()
            _populate_school_slugs()

            super_admin = User.query.filter_by(role='super_admin').first()
            if not super_admin:
                super_admin = User(
                    username='superadmin',
                    role='super_admin',
                    full_name='Super Administrateur',
                    email='superadmin@gescoapp.com',
                )
                super_admin.set_password('super123')
                db.session.add(super_admin)
                db.session.commit()
                print('Super admin créé : superadmin / super123')
            else:
                print(f"Super admin existe déjà : {super_admin.username}")

            print("Aucune donnée démo n'est créée automatiquement.")
            print("Créez les écoles et utilisateurs depuis l'interface d'administration.")
            print('\nConfiguration terminée\n')
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erreur : {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Initialise la base et lance l'application."""
    print('GescoApp - Démarrage')
    print('=' * 50)

    if init_db():
        print("Lancement de l'application...")
        print('=' * 50)
        print('Accédez à : http://localhost:5000')
        print('Page de connexion : http://localhost:5000/login')
        print('=' * 50)
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Impossible d'initialiser la base de données")
        sys.exit(1)


if __name__ == '__main__':
    main()
