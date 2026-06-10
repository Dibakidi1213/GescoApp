from app import app
from models import Section

with app.app_context():
    secs = Section.query.filter(Section.level.like('4%')).filter(Section.name.ilike('%scien%')).all()
    if not secs:
        print('NO_RESULTS')
    for s in secs:
        print(f"{s.id}|{s.name}|{s.level}")
