#!/usr/bin/env python3
"""Créer un utilisateur admin pour tester"""

from app import app, db, User, School
from werkzeug.security import generate_password_hash

with app.app_context():
    # Créer l'admin
    admin = User(
        username='admin_test',
        password=generate_password_hash('admin_test'),
        is_super_admin=True
    )
    
    # Créer une école
    school = School(
        name='École de Test',
        slug='ecole-test',
        province='Kinshasa',
        city='Kinshasa'
    )
    
    db.session.add(admin)
    db.session.add(school)
    db.session.commit()
    
    print("✅ Utilisateur admin créé:")
    print(f"   Username: admin_test")
    print(f"   Password: admin_test")
    print(f"\n✅ École créée: {school.name} (ID: {school.id})")
