from app import app
from models import BulletinConfig, BulletinBranch, db

with app.app_context():
    # Récupérer la config validée (ID 1)
    source_config = BulletinConfig.query.get(1)
    
    if not source_config:
        print("❌ Config ID 1 non trouvée!")
        exit(1)
    
    source_branches = source_config.branches.order_by(BulletinBranch.order).all()
    print(f"✓ Config source (ID 1) trouvée avec {len(source_branches)} branches")
    print()
    
    # Récupérer toutes les autres configs
    target_configs = BulletinConfig.query.filter(BulletinConfig.id != 1).all()
    print(f"Réinitialisation de {len(target_configs)} configurations...")
    print()
    
    for config in target_configs:
        print(f"Config ID {config.id} (Section {config.section_id}, Level {config.level}):")
        
        # Supprimer les branches existantes
        old_branch_count = len(config.branches.all())
        BulletinBranch.query.filter_by(config_id=config.id).delete()
        print(f"  → Suppression de {old_branch_count} branches existantes")
        
        # Copier les branches de la config source
        for branch in source_branches:
            new_branch = BulletinBranch(
                config_id=config.id,
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
        
        # Réinitialiser le statut de validation
        config.validated = False
        config.validated_at = None
        config.validated_by_user_id = None
        
        print(f"  → Ajout de {len(source_branches)} nouvelles branches")
        print(f"  → Statut validation réinitialisé à False")
        print()
    
    # Valider les changements
    db.session.commit()
    
    print("✅ Réinitialisation terminée avec succès!")
    print()
    
    # Afficher le résumé
    for config in BulletinConfig.query.all():
        print(f"Config ID {config.id}: {len(config.branches.all())} branches, Validé: {config.validated}")
