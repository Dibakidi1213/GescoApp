from app import app
from models import db, Section, Course, Student, Grade, BulletinConfig, BulletinBranch, User
from datetime import datetime

with app.app_context():
    # Get or create test section
    section = Section.query.filter_by(name='Section Test', school_id=1).first()
    if not section:
        section = Section(name='Section Test', level='Primaire', class_name='P4', school_id=1)
        db.session.add(section)
        db.session.flush()
    
    # Get or create test course
    prof = User.query.filter_by(username='testprof').first()
    course = Course.query.filter_by(title='Mathematics', section_id=section.id, professor_id=prof.id, school_id=1).first()
    if not course:
        course = Course(
            title='Mathematics',
            section_id=section.id,
            professor_id=prof.id,
            school_id=1
        )
        db.session.add(course)
        db.session.flush()
    
    # Create or get bulletin config for this section/level
    config = BulletinConfig.query.filter_by(school_id=1, section_id=section.id, level=section.level).first()
    if not config:
        config = BulletinConfig(
            school_id=1,
            section_id=section.id,
            level=section.level,
            created_at=datetime.now()
        )
        db.session.add(config)
        db.session.flush()
    
    # Create bullet branch (domain/subdomain configuration)
    branch = BulletinBranch.query.filter_by(config_id=config.id, name='Mathematics').first()
    if not branch:
        branch = BulletinBranch(
            config_id=config.id,
            domain='Academic',
            subdomain='Math',
            name='Mathematics',
            order=1,
            max_period_1=10,
            max_period_2=10,
            max_exam_1=20,
            max_period_3=10,
            max_period_4=10,
            max_exam_2=20,
            include_period_1=True,
            include_period_2=True,
            include_comp_1=True,
            include_period_3=True,
            include_period_4=True,
            include_comp_2=True
        )
        db.session.add(branch)
        db.session.flush()
    
    # Link course to branch
    if not course.branch_id:
        course.branch_id = branch.id
    
    # Create test students
    for i in range(1, 4):
        student = Student.query.filter_by(first_name=f'Student', last_name=f'{i}', school_id=1).first()
        if not student:
            student = Student(
                first_name=f'Student',
                last_name=f'{i}',
                school_id=1,
                section_id=section.id,
                serial_number=f'STU00{i}'
            )
            db.session.add(student)
            db.session.flush()
    
    db.session.commit()
    print(f"✓ Test data created:")
    print(f"  - Section: {section.name} ({section.level} {section.class_name})")
    print(f"  - Course: {course.title} (ID: {course.id})")
    print(f"  - Branch: {branch.name} (ID: {branch.id})")
    print(f"  - 3 test students created")
    print(f"\nCourse ID for testing: {course.id}")

