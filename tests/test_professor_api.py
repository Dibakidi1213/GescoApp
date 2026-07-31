#!/usr/bin/env python
# Test API endpoints for professors

from app import app, db
from models import Course, Section, User
from flask import json

with app.app_context():
    # Get olivier dibakidi (ID 3)
    olivier = User.query.get(3)
    print(f"Testing API endpoints for professor: {olivier.full_name}")
    print(f"School ID: {olivier.school_id}")
    print("="*80)
    
    # Get his courses
    courses = Course.query.filter_by(professor_id=olivier.id).all()
    print(f"\nTotal courses: {len(courses)}")
    for course in courses:
        section_name = f"{course.section.name}" if course.section else "[NO SECTION]"
        print(f"  - {course.title} (Section: {section_name})")
    
    # Get sections where he has courses (with section_id)
    sections = db.session.query(Section).join(Course).filter(
        Course.professor_id == olivier.id,
        Course.school_id == olivier.school_id,
        Course.section_id.isnot(None)
    ).distinct().all()
    
    print(f"\nSections with courses: {len(sections)}")
    for section in sections:
        print(f"  - {section.name} ({section.level} {section.class_name}) - ID: {section.id}")
    
    # Simulate API response
    print("\nAPI /api/sections response:")
    response_data = [
        {
            'id': s.id,
            'name': s.name,
            'level': s.level,
            'class_name': s.class_name
        }
        for s in sections
    ]
    print(json.dumps(response_data, indent=2, default=str))
