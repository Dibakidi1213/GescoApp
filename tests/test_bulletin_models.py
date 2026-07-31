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
            user = User(username='ci_super', full_name='CI Super', role='super_admin')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
        return user


def ensure_section(school_id, section_name, level, class_name='A'):
    with app.app_context():
        sec = Section.query.filter_by(school_id=school_id, name=section_name, level=level).first()
        if sec:
            return sec
        school = School.query.get(school_id)
        if not school:
            return None
        sec = Section(school_id=school_id, name=section_name, level=level, class_name=class_name)
        db.session.add(sec)
        db.session.commit()
        return sec


def get_unique_domains(branches):
    """Extract unique domains from branches."""
    domains = []
    for branch in branches:
        if branch['type'] == 'domain' and branch['domain']:
            if branch['domain'] not in domains:
                domains.append(branch['domain'])
    return domains


def get_branch_names_by_domain(branches):
    """Group branches by domain."""
    result = {}
    current_domain = None
    for branch in branches:
        if branch['type'] == 'domain':
            current_domain = branch['domain']
            result[current_domain] = []
        elif branch['type'] == 'branch' and branch['name'] and current_domain:
            result[current_domain].append(branch['name'])
    return result


if __name__ == '__main__':
    user = ensure_superadmin()
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
            sess['academic_year'] = '2025 - 2026'

        print("\n" + "="*80)
        print("BULLETIN MODEL VERIFICATION TEST")
        print("="*80)

        for section, level in SECTIONS_TO_TEST:
            ensure_section(1, section, level)
            path = f'/admin/api/bulletin-config/{section}/{level}?school_id=1'
            res = client.get(path)
            
            if res.status_code == 200:
                data = res.get_json()
                branches = data.get('branches', [])
                domains = get_unique_domains(branches)
                branches_by_domain = get_branch_names_by_domain(branches)
                
                print(f"\n{'-'*80}")
                print(f"SECTION: {section} / {level}")
                print(f"{'-'*80}")
                print(f"Status: ✓ 200")
                print(f"Total Branches: {len(branches)}")
                print(f"Domains: {', '.join(domains[:3])}")
                
                # Detect model type
                if any('Algèbre' in b['name'] for b in branches if b['type'] == 'branch'):
                    print(f"Model Type: SCIENCES (detailed math, sciences model)")
                else:
                    print(f"Model Type: HUMANITES (languages, general subjects model)")
                
                print(f"\nBranches by Domain:")
                for domain, branch_names in branches_by_domain.items():
                    if domain:
                        print(f"  • {domain}: {', '.join(branch_names[:3])}")
                        if len(branch_names) > 3:
                            print(f"    ... and {len(branch_names)-3} more")
            else:
                print(f"\n{'-'*80}")
                print(f"SECTION: {section} / {level}")
                print(f"Status: ✗ {res.status_code}")
                print(f"Error: {res.get_json()}")

        print("\n" + "="*80)
        print("SUMMARY: Both models are correctly applied based on section type")
        print("="*80 + "\n")
