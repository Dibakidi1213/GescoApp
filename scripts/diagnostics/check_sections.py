from app import app
from models import Section

SECTIONS = [
    ('LATIN PHILO','3ème'),
    ('ELECTRICITE','2ème'),
    ('CONSTRUCTION','4ème'),
]

with app.app_context():
    for name, level in SECTIONS:
        sec = Section.query.filter_by(school_id=1, name=name, level=level).first()
        print(f"{name} {level}:", 'FOUND' if sec else 'MISSING')
