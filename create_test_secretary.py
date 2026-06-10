from app import app
from models import db, User

with app.app_context():
    # Check if test secretary already exists
    test_sec = User.query.filter_by(username='testsec').first()
    
    if test_sec:
        print("Test secretary already exists, resetting password...")
        test_sec.set_password('testsec')
        db.session.commit()
    else:
        # Create new test secretary
        test_sec = User(
            username='testsec',
            role='secretary',
            full_name='Test Secretary',
            email='sec@example.com',
            school_id=1
        )
        test_sec.set_password('testsec')
        db.session.add(test_sec)
        db.session.commit()
    
    print(f"✓ Test secretary created/updated: username=testsec, password=testsec, ID={test_sec.id}")
