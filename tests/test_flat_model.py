from app import app, db
from models import User, Section

SECTIONS_TO_TEST = [
    ('LATIN PHILO', '3ème'),      
    ('ELECTRICITE', '2ème'),      
    ('CONSTRUCTION', '4ème'),     
    ('SCIENCES', '1ère'),         
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
        sec = Section(school_id=school_id, name=section_name, level=level, class_name=class_name)
        db.session.add(sec)
        db.session.commit()
        return sec


if __name__ == '__main__':
    user = ensure_superadmin()
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
            sess['academic_year'] = '2025 - 2026'

        print("\n" + "="*90)
        print("BULLETIN MODELS - STRUCTURE COMPARISON")
        print("="*90)

        for section, level in SECTIONS_TO_TEST:
            ensure_section(1, section, level)
            path = f'/admin/api/bulletin-config/{section}/{level}?school_id=1'
            res = client.get(path)
            
            if res.status_code == 200:
                data = res.get_json()
                branches = data.get('branches', [])
                
                # Get only branch type items
                branch_items = [b for b in branches if b['type'] == 'branch']
                domain_items = [b for b in branches if b['type'] == 'domain']
                subdomain_items = [b for b in branches if b['type'] == 'subdomain']
                
                # Detect model type
                is_sciences = any('Algèbre' in b['name'] for b in branch_items)
                model_type = 'SCIENCES (35 branches)' if is_sciences else 'HUMANITES (10 branches plats)'
                structure = 'Avec domaines/sous-domaines' if domain_items or subdomain_items else '✓ PLAT - SANS domaines'
                
                print(f"\n{section} / {level}")
                print(f"{'─'*90}")
                print(f"  Modèle: {model_type}")
                print(f"  Structure: {structure}")
                print(f"  Domaines: {len(domain_items)} | Sous-domaines: {len(subdomain_items)} | Branches: {len(branch_items)}")
                
                if not (domain_items or subdomain_items):
                    # Flat model - list all branches
                    print(f"  Branches:")
                    for i, b in enumerate(branch_items, 1):
                        max_p = int(b['max_period_1']) if isinstance(b['max_period_1'], (int, float)) else 0
                        max_e = int(b['max_exam_1']) if isinstance(b['max_exam_1'], (int, float)) else 0
                        print(f"    {i:2d}. {b['name']:30s} (Max P:{max_p:3d}, Max E:{max_e:3d})")

        print("\n" + "="*90)
        print("✓ Non-SCIENCES sections use modèle PLAT (sans domaines ni sous-domaines)")
        print("✓ SCIENCES section continue avec modèle détaillé (avec domaines/sous-domaines)")
        print("="*90 + "\n")
