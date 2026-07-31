#!/usr/bin/env python
"""Quick database connection test"""
from app import create_app, db

app = create_app()
with app.app_context():
    print('✅ App initialized successfully')
    try:
        # Try to execute a simple query
        from models import School
        schools = School.query.first()
        print(f'✅ Database connection working')
        print(f'✅ Sample school: {schools.name if schools else "No schools yet"}')
    except Exception as e:
        print(f'❌ Database error: {str(e)}')
