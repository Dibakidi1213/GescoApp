from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(role='super_admin').first()
    if admin:
        admin.password_hash = generate_password_hash('superadmin123')
        admin.is_active = True
        admin.login_failed_attempts = 0
        admin.must_change_password = False
        db.session.commit()
        print(f"Password reset for {admin.username}. New password is: superadmin123")
    else:
        # Create a new superadmin just in case
        admin = User(
            username='superadmin',
            password_hash=generate_password_hash('superadmin123'),
            role='super_admin',
            full_name='Super Admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Created new superadmin. Username: superadmin, Password: superadmin123")
