from app import app, db
from models import User, Section, School
import json

SECTIONS_TO_TEST = [
    ('LATIN PHILO', '3ème'),      # Non-SCIENCES: should use humanités model
    ('ELECTRICITE', '2ème'),      # Non-SCIENCES: should use humanités model
    ('CONSTRUCTION', '4ème'),     # Non-SCIENCES: should use humanités model
    ('SCIENCES', '1ère'),         # SCIENCES: should use sciences model
]


def ensure_superadmin():
    with app.app_context():
        user = User.query.filter_by(role='super_admin').first()
        if not user:
            print('No super_admin found. Creating temporary super_admin user `ci_super` with password `password`.')
            user = User(username='ci_super', full_name='CI Super', role='super_admin')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
        return user


def ensure_section(school_id, section_name, level, class_name='A'):
    with app.app_context():
        # Normalize level string as stored in DB (use given)
        sec = Section.query.filter_by(school_id=school_id, name=section_name, level=level).first()
        if sec:
            return sec
        # Verify school exists
        school = School.query.get(school_id)
        if not school:
            print(f"School id={school_id} not found, skipping creation of section {section_name} {level}")
            return None
        sec = Section(school_id=school_id, name=section_name, level=level, class_name=class_name)
        db.session.add(sec)
        db.session.commit()
        print(f"Created section: {section_name} / {level} for school {school_id}")
        return sec


def extract_branches_summary(branches):
    """Extract a summary of branch names for quick verification."""
    return [b['name'] for b in branches if b['type'] == 'branch' and b['name']]


if __name__ == '__main__':
    user = ensure_superadmin()
    with app.test_client() as client:
        # Authenticate by setting session user id
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
            # Ensure academic year present
            sess['academic_year'] = sess.get('academic_year', '2025 - 2026')

        for section, level in SECTIONS_TO_TEST:
            # Ensure the test section exists for school_id=1
            ensure_section(1, section, level)
            path = f'/admin/api/bulletin-config/{section}/{level}?school_id=1'
            print(f'\n{"="*70}')
            print(f'REQUEST -> {path}')
            print(f'{"="*70}')
            res = client.get(path)
            print(f'Status: {res.status_code}')
            try:
                data = res.get_json()
                if res.status_code == 200:
                    branches = data.get('branches', [])
                    branches_summary = extract_branches_summary(branches)
                    print(f'Section: {data.get("section_name")}')
                    print(f'Total Branches: {len(branches)}')
                    print(f'Branch Names (first 10): {branches_summary[:10]}')
                    print(f'\nModel Type: {"HUMANITES" if "Français" in branches_summary else "SCIENCES"}')
                else:
                    print(f'Error: {json.dumps(data, ensure_ascii=False, indent=2)}')
            except Exception as e:
                print(f'Response Text: {res.get_data(as_text=True)[:1000]}')
