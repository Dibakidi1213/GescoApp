from app import app
from models import db, User, Section, Course
with app.app_context():
    prof = User.query.filter(User.full_name.ilike('%BIKA%')).first()
    print('prof=', prof.id if prof else None, prof.full_name if prof else None, prof.role if prof else None, prof.school_id if prof else None)
    if prof:
        sections = Section.query.join(Course).filter(Course.professor_id==prof.id).distinct().all()
        print('sections for professor:', [(s.name,s.level,s.class_name) for s in sections])
        courses = Course.query.filter_by(professor_id=prof.id).all()
        print('courses count', len(courses))
        for c in courses[:20]:
            print(c.id, c.title, c.section_id, c.section.name if c.section else None, c.section.level if c.section else None, c.section.class_name if c.section else None)
