#!/usr/bin/env python
# Check current courses state

from app import app, db
from models import Course, Section, User

with app.app_context():
    courses = Course.query.all()
    print(f"Total courses: {len(courses)}")
    print("\n" + "="*80)
    
    for course in courses:
        section_name = f"{course.section.name}" if course.section else "[NO SECTION]"
        prof_name = f"{course.professor.full_name}" if course.professor else "[NO PROFESSOR]"
        print(f"ID: {course.id:<3} | Title: {course.title:<20} | Section: {section_name:<30} | Prof: {prof_name}")
    
    print("\n" + "="*80)
    print("\nCourses without section assigned:")
    unassigned = Course.query.filter_by(section_id=None).all()
    print(f"Total: {len(unassigned)}")
    for course in unassigned:
        prof_name = f"{course.professor.full_name}" if course.professor else "[NO PROFESSOR]"
        print(f"  - {course.title} (Prof: {prof_name})")
