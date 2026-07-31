from app import app
from models import db, User

with app.app_context():
    # Check if test professor already exists
    test_prof = User.query.filter_by(username='testprof').first()
    
    if test_prof:
        print("Test professor already exists, resetting password...")
        test_prof.set_password('testpass')
        db.session.commit()
    else:
        # Create new test professor
        test_prof = User(
            username='testprof',
            role='professor',
            full_name='Test Professor',
            email='test@example.com',
            school_id=1  # Assuming school 1 exists
        )
        test_prof.set_password('testpass')
        db.session.add(test_prof)
        db.session.commit()
    
    print(f"✓ Test professor created/updated: username=testprof, password=testpass")
