from app import app
from models import db, User

with app.app_context():
    testprof = User.query.filter_by(username='testprof').first()
    if testprof:
        print(f"✓ Found testprof: ID={testprof.id}, Role={testprof.role}, School={testprof.school_id}")
    else:
        print("✗ testprof not found")
