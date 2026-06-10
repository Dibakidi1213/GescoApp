#!/usr/bin/env python3
"""
Script de configuration initiale pour GescoApp
Crée un super administrateur et une école de démonstration
"""

from app import app, db
from models import User, School

def create_super_admin():
    """Crée un super administrateur"""
    print("Création du super administrateur...")

    # Vérifier si un super admin existe déjà
    existing_super = User.query.filter_by(role='super_admin').first()
    if existing_super:
        print(f"Un super administrateur existe déjà : {existing_super.username}")
        return existing_super

    # Créer le super admin
    super_admin = User(
        username='superadmin',
        role='super_admin',
        full_name='Super Administrateur',
        email='superadmin@gescoapp.com'
    )
    super_admin.set_password('super123')

    db.session.add(super_admin)
    db.session.commit()

    print("✅ Super administrateur créé :")
    print("   Username: superadmin")
    print("   Password: super123")
    print("   Rôle: Super Administrateur")

    return super_admin

def create_demo_school():
    """Crée une école de démonstration"""
    print("\nCréation d'une école de démonstration...")

    # Vérifier si une école existe déjà
    existing_school = School.query.filter_by(name='École Démo').first()
    if existing_school:
        print(f"L'école de démonstration existe déjà : {existing_school.name}")
        return existing_school

    # Créer l'école
    school = School(
        name='École Démo',
        address='123 Rue de l\'Éducation, Ville',
        phone='+225 01 02 03 04 05',
        email='contact@ecole-demo.com',
        logo='https://example.com/logo.png'
    )

    db.session.add(school)
    db.session.commit()

    print("✅ École de démonstration créée :")
    print(f"   Nom: {school.name}")
    print(f"   Adresse: {school.address}")
    print(f"   Email: {school.email}")

    return school

def create_school_admin(school):
    """Crée un administrateur pour l'école"""
    print(f"\nCréation d'un administrateur pour {school.name}...")

    # Vérifier si un admin existe déjà pour cette école
    existing_admin = User.query.filter_by(school_id=school.id, role='school_admin').first()
    if existing_admin:
        print(f"Un administrateur existe déjà pour cette école : {existing_admin.username}")
        return existing_admin

    # Créer l'admin d'école
    school_admin = User(
        school_id=school.id,
        username='admin_demo',
        role='school_admin',
        full_name='Administrateur Démo',
        email='admin@ecole-demo.com'
    )
    school_admin.set_password('admin123')

    db.session.add(school_admin)
    db.session.commit()

    print("✅ Administrateur d'école créé :")
    print("   Username: admin_demo")
    print("   Password: admin123")
    print(f"   École: {school.name}")
    print("   Rôle: Administrateur d'école")

    return school_admin

def main():
    """Fonction principale"""
    print("🚀 Configuration initiale de GescoApp")
    print("=" * 40)

    with app.app_context():
        try:
            # Créer les tables si elles n'existent pas
            db.create_all()
            print("✅ Tables de base de données vérifiées/créées")

            # Créer le super admin
            super_admin = create_super_admin()

            # Créer l'école de démo
            demo_school = create_demo_school()

            # Créer l'admin d'école
            school_admin = create_school_admin(demo_school)

            print("\n" + "=" * 40)
            print("🎉 Configuration terminée avec succès !")
            print("\nComptes créés :")
            print("1. Super Admin : superadmin / super123")
            print("2. Admin École : admin_demo / admin123 (pour École Démo)")
            print("\nVous pouvez maintenant :")
            print("- Vous connecter en tant que superadmin pour gérer les écoles")
            print("- Vous connecter en tant que admin_demo pour gérer l'école démo")
            print("- Créer de nouvelles écoles et utilisateurs selon vos besoins")

        except Exception as e:
            print(f"❌ Erreur lors de la configuration : {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    main()