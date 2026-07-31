from app import app
from models import BulletinConfig, BulletinBranch, Section, db

with app.app_context():
    # Récupérer la config source (ID 1 ou 2)
    source_config = BulletinConfig.query.get(1)
    source_branches = source_config.branches.order_by(BulletinBranch.order).all()
    
    print(f"Config source: {source_config.id} ({len(source_branches)} branches)")
    print()
    
    # Vérifier les sections LATIN PHILO manquantes
    latin_philo_sections = Section.query.filter_by(school_id=1, name='LATIN PHILO').all()
    print(f"Sections LATIN PHILO trouvées:")
    for section in latin_philo_sections:
        config_exists = BulletinConfig.query.filter_by(
            school_id=1,
            section_id=section.id,
            level=section.level,
        ).first()
        status = "✓ Config existe" if config_exists else "✗ Config MANQUANTE"
        print(f"  Level {section.level}, Class {section.class_name} (Section ID {section.id}): {status}")
    
    print()
    print("=== Création des configurations manquantes ===")
    
    # Créer les configs manquantes
    for section in latin_philo_sections:
        config_exists = BulletinConfig.query.filter_by(
            school_id=1,
            section_id=section.id,
            level=section.level,
        ).first()
        
        if not config_exists:
            # Créer une nouvelle config
            new_config = BulletinConfig(
                school_id=1,
                section_id=section.id,
                level=section.level,
                academic_year='2025 - 2026',
            )
            db.session.add(new_config)
            db.session.flush()
            
            # Copier les branches
            for branch in source_branches:
                new_branch = BulletinBranch(
                    config_id=new_config.id,
                    type=branch.type,
                    name=branch.name,
                    domain=branch.domain,
                    subdomain=branch.subdomain,
                    order=branch.order,
                    max_value=branch.max_value,
                    max_period_1=branch.max_period_1,
                    max_period_2=branch.max_period_2,
                    max_exam_1=branch.max_exam_1,
                    max_period_3=branch.max_period_3,
                    max_period_4=branch.max_period_4,
                    max_exam_2=branch.max_exam_2,
                    include_period_1=branch.include_period_1,
                    include_period_2=branch.include_period_2,
                    include_comp_1=branch.include_comp_1,
                    include_period_3=branch.include_period_3,
                    include_period_4=branch.include_period_4,
                    include_comp_2=branch.include_comp_2,
                )
                db.session.add(new_branch)
            
            print(f"  ✓ Config créée pour Level {section.level}, Class {section.class_name} (Section ID {section.id})")
    
    db.session.commit()
    
    print()
    print("=== Vérification finale ===")
    for section in latin_philo_sections:
        config = BulletinConfig.query.filter_by(
            school_id=1,
            section_id=section.id,
            level=section.level,
        ).first()
        branches_count = len(config.branches.all()) if config else 0
        print(f"  Level {section.level}: {branches_count} branches")
