from app import app
from models import BulletinConfig, BulletinBranch, db

with app.app_context():
    configs = BulletinConfig.query.all()
    print(f"Nombre de configurations de bulletins: {len(configs)}\n")
    
    if configs:
        for config in configs[:5]:  # Afficher les 5 premiers
            print(f"Config ID: {config.id}")
            print(f"  School: {config.school_id}")
            print(f"  Section: {config.section_id}")
            print(f"  Level: {config.level}")
            print(f"  Year: {config.academic_year}")
            print(f"  Validé: {config.validated}")
            print(f"  Branches: {len(config.branches.all())}")
            print()
