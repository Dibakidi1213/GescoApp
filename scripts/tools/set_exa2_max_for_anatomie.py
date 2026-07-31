import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Course, Section, BulletinBranch

with app.app_context():
    section = Section.query.filter_by(name='EDUCATION DE BASE', level='7', class_name='A').first()
    if not section:
        print('Section EDUCATION DE BASE / 7 / A not found')
        sections = Section.query.order_by(Section.name, Section.level, Section.class_name).limit(10).all()
        print('Sample sections:')
        for s in sections:
            print('-', s.name, s.level, s.class_name)
        sys.exit(1)

    course = Course.query.filter_by(section_id=section.id, title='Anatomie').first()
    if not course:
        print('Course Anatomie not found in section', section.name)
        courses = Course.query.filter_by(section_id=section.id).limit(20).all()
        print('Courses in section:')
        for c in courses:
            print('-', c.title)
        sys.exit(1)

    print('Found course:', course.title, 'id', course.id, 'branch_id', course.branch_id)
    branch = None
    if course.branch_id:
        branch = BulletinBranch.query.get(course.branch_id)
        if branch:
            print('Branch from course.branch_id:', branch.name, 'max_exam_2=', branch.max_exam_2)
    if not branch:
        # Try to find within bulletin config branches
        configs = course.section and course.section.school and course.section.school.bulletin_configs
        # naive search: find branch by title in BulletinBranch
        b = BulletinBranch.query.filter(BulletinBranch.name.ilike('%Anatomie%')).first()
        if b:
            branch = b
            print('Found branch by name:', branch.name, 'max_exam_2=', branch.max_exam_2)

    if not branch:
        print('No branch found to update. Aborting.')
        sys.exit(1)

    if float(branch.max_exam_2 or 0) == 20.0:
        print('max_exam_2 already 20 for branch', branch.name)
    else:
        print('Updating branch', branch.name, 'max_exam_2 from', branch.max_exam_2, 'to 20')
        branch.max_exam_2 = 20
        db.session.commit()
        print('Updated. New value:', branch.max_exam_2)
