from app import app
from models import db, User

with app.app_context():
    users = User.query.limit(10).all()
    print("=== Users in Database ===")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}, School: {user.school_id}")
    
    # Try to find a professor
    prof = User.query.filter_by(role='professor').first()
    if prof:
        print(f"\n✓ Found professor: {prof.username}")
    else:
        print("\n✗ No professor found")
