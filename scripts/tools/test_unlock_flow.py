import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import School, User, Section, Course, Student, Grade, Notification
from flask import url_for

period = '1èP'

with app.app_context():
    # Ensure a school
    school = School.query.filter_by(slug='test-school').first()
    if not school:
        school = School(name='Test School', slug='test-school', is_active=True)
        db.session.add(school)
        db.session.commit()

    # Ensure secretary
    secretary = User.query.filter_by(username='sec_test').first()
    if not secretary:
        secretary = User(school_id=school.id, username='sec_test', full_name='Secretarie Test', role='secretary')
        secretary.set_password('secret')
        db.session.add(secretary)
        db.session.commit()

    # Ensure professor
    prof = User.query.filter_by(username='prof_test').first()
    if not prof:
        prof = User(school_id=school.id, username='prof_test', full_name='Prof Test', role='professor')
        prof.set_password('prof')
        db.session.add(prof)
        db.session.commit()

    # Ensure section
    section = Section.query.filter_by(school_id=school.id, name='A', level='1', class_name='A').first()
    if not section:
        section = Section(school_id=school.id, name='A', level='1', class_name='A')
        db.session.add(section)
        db.session.commit()

    # Ensure course
    course = Course.query.filter_by(school_id=school.id, title='Math', section_id=section.id).first()
    if not course:
        course = Course(school_id=school.id, title='Math', section_id=section.id, professor_id=prof.id)
        db.session.add(course)
        db.session.commit()

    # Ensure students and grades
    students = Student.query.filter_by(school_id=school.id, section_id=section.id).all()
    if not students:
        s1 = Student(school_id=school.id, first_name='Alice', last_name='Dupont', section_id=section.id)
        s2 = Student(school_id=school.id, first_name='Bob', last_name='Martin', section_id=section.id)
        db.session.add_all([s1, s2])
        db.session.commit()
        students = [s1, s2]

    # Create grades and mark submitted
    for student in students:
        g = Grade.query.filter_by(school_id=school.id, student_id=student.id, course_id=course.id, period=period).first()
        if not g:
            g = Grade(school_id=school.id, student_id=student.id, course_id=course.id, period=period, value=12.5, submitted=True, academic_year='2025 - 2026')
            db.session.add(g)
    db.session.commit()

    # Use Flask test client to login as secretary and call unlock endpoint
    client = app.test_client()
    # Disable CSRF for test client
    app.config['WTF_CSRF_ENABLED'] = False
    login_url = f"/login"
    # Instead of posting to /login, set the session so client is authenticated as secretary
    with client.session_transaction() as sess:
        sess['_user_id'] = str(secretary.id)
        sess['_fresh'] = True
    print('test client session set for secretary id', secretary.id)

    # Call the unlock view function directly within a test request context and logged-in user
    from routes.secretary import unlock_period
    from flask_login import login_user

    with app.test_request_context(f"/{school.slug}/secretary/api/unlock-period/{course.id}", method='POST', json={'period': period}):
        login_user(secretary)
        resp = unlock_period(course.id, school_slug=school.slug)
        try:
            print('direct call response:', resp.get_json())
        except Exception:
            print('direct call response:', resp)

    # Check notifications for professor
    notifs = Notification.query.filter_by(school_id=school.id, recipient_id=prof.id).order_by(Notification.created_at.desc()).limit(5).all()
    for n in notifs:
        print('Notif:', n.id, n.title, n.message, n.url, n.is_read)

    # Verify grades submitted flag
    grades = Grade.query.filter_by(school_id=school.id, course_id=course.id, period=period).all()
    for g in grades:
        print('Grade', g.id, 'submitted=', g.submitted)

    print('Done')
